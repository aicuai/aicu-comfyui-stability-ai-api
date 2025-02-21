import os
import json
import requests
from typing import Optional, Dict, Any, Union
import torch
import numpy as np
from PIL import Image
import io

class StabilityAPIClient:
    """
    Client class for communicating with the Stability AI API
    """
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client

        Parameters:
        -----------
        api_key : str, optional
            Stability AI API key. If not provided, will be loaded from environment variables
        """
        from .config_manager import ConfigManager
        
        # Priority order for obtaining the API key:
        # 1. Directly specified API key
        # 2. API key from environment variables
        # 3. API key from config.ini
        self.api_key = api_key or ConfigManager().get_api_key()
        
        if not self.api_key or self.api_key == "your_api_key_here":
            raise ValueError("API key must be provided either directly, through STABILITY_API_KEY environment variable, or in config.ini")
        
        self.base_url = "https://api.stability.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Optional[Dict[str, Any]] = None,
                     files: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """Make an API request

        Parameters:
        -----------
        method : str
            HTTP method ('GET', 'POST', etc.)
        endpoint : str
            API endpoint
        data : dict, optional
            Request body
        files : dict, optional
            Files to upload
        headers : dict, optional
            Additional headers
            
        Returns:
        --------
        requests.Response
            API response
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        if headers:
            # Remove Content-Type header (requests will set it automatically)
            if "Content-Type" in headers:
                del headers["Content-Type"]
            request_headers.update(headers)
            
        # Make the request
        response = requests.request(
            method=method,
            url=url,
            data=data,
            files=files,
            headers=request_headers
        )
            
        if response.status_code not in [200, 202]:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
        return response

    def tensor_to_pil(self, image: torch.Tensor) -> Image.Image:
        """Convert a PyTorch tensor to a PIL image

        Parameters:
        -----------
        image : torch.Tensor
            Image tensor to convert. Supports the following formats:
            - [H,W,C] : RGB image
            - [B,H,W,C] : RGB batch image
            - [H,W] : Grayscale image/mask
            - [B,H,W] : Grayscale batch image/mask
            - [1,1,H,W] : Special mask format
            
        Returns:
        --------
        PIL.Image
            Converted PIL image
        """
        # Get the tensor shape
        shape = image.shape
        
        # Remove batch dimension (if necessary)
        if len(shape) == 4:
            if shape[0] == 1:  # Batch size 1
                if shape[1] == 1:  # Special mask format
                    image = image.squeeze(0).squeeze(0)  # [1,1,H,W] -> [H,W]
                else:
                    image = image.squeeze(0)  # [1,H,W,C] -> [H,W,C]
            else:
                raise ValueError(f"Only batch size 1 is supported: {shape}")
        
        # Convert tensor to numpy array
        img_array = image.cpu().numpy()
        
        # Normalize data type and value range
        if img_array.dtype != np.uint8:
            img_array = (img_array * 255).astype(np.uint8)
        
        # Create a PIL image in the correct mode based on the shape
        if len(img_array.shape) == 2:  # [H,W]
            pil_image = Image.fromarray(img_array, mode='L')
        elif len(img_array.shape) == 3:  # [H,W,C]
            if img_array.shape[2] == 1:  # Grayscale
                pil_image = Image.fromarray(img_array.squeeze(2), mode='L')
            elif img_array.shape[2] == 3:  # RGB
                pil_image = Image.fromarray(img_array, mode='RGB')
            else:
                raise ValueError(f"Unsupported number of channels: {img_array.shape[2]}")
        else:
            raise ValueError(f"Unsupported number of dimensions: {len(img_array.shape)}")
            
        return pil_image

    def pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """Convert a PIL image to a PyTorch tensor

        Parameters:
        -----------
        image : PIL.Image
            Image to convert
            
        Returns:
        --------
        torch.Tensor
            Converted image tensor [H,W,C]
        """
        # Convert PIL image to numpy array
        img_array = np.array(image).astype(np.float32) / 255.0
        
        # Add channel dimension for grayscale images
        if len(img_array.shape) == 2:
            img_array = np.expand_dims(img_array, axis=2)
        
        # Convert numpy array to PyTorch tensor
        img_tensor = torch.from_numpy(img_array)
        
        return img_tensor

    def image_to_bytes(self, image: Union[torch.Tensor, Image.Image], format: str = 'PNG') -> bytes:
        """Convert an image to a byte array

        Parameters:
        -----------
        image : Union[torch.Tensor, Image.Image]
            Image to convert (PyTorch tensor or PIL image)
        format : str
            Output format ('PNG', 'JPEG', 'WEBP')
            
        Returns:
        --------
        bytes
            Image byte array
        """
        if isinstance(image, torch.Tensor):
            image = self.tensor_to_pil(image)
            
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        return img_byte_arr.getvalue()

    def bytes_to_tensor(self, image_bytes: bytes) -> torch.Tensor:
        """Convert a byte array to an image tensor

        Parameters:
        -----------
        image_bytes : bytes
            Image byte array
            
        Returns:
        --------
        torch.Tensor
            Converted image tensor [B,H,W,C] format
            B: Batch size (1)
            H: Height
            W: Width
            C: Number of channels (3: RGB)
            Values are in the range 0-1, float32 type
        """
        # Create a PIL image from the byte array
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB format
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Check image size
        width, height = image.size
        print(f"Image size: {width}x{height}")
        
        # Convert PIL image to numpy array and normalize to 0-1 range
        img_array = np.array(image).astype(np.float32) / 255.0
        
        # Add batch dimension [B,H,W,C]
        img_tensor = torch.from_numpy(img_array)
        img_tensor = img_tensor.unsqueeze(0)  # (1, H, W, C)
        
        # Close the PIL image to prevent memory leaks
        image.close()
        
        print(f"Tensor shape: {img_tensor.shape}, dtype: {img_tensor.dtype}")  # Debug information
        return img_tensor

    def check_balance(self) -> float:
        """Check the account balance

        Returns:
        --------
        float
            Available credit balance
        """
        response = self._make_request('GET', '/v1/user/balance')
        return response.json()['credits']
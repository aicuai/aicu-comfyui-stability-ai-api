import os
import configparser
from typing import Optional

class ConfigManager:
    """A class to manage configuration files"""
    
    _instance = None
    
    def __new__(cls):
        """Implementation of the singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize (singleton, executed only once)"""
        if self._initialized:
            return
            
        self._initialized = True
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(__file__), "config.ini")
        
        # Create the configuration file if it does not exist
        if not os.path.exists(self.config_path):
            self.config["stability"] = {
                "api_key": "your_api_key_here"
            }
            with open(self.config_path, "w") as f:
                self.config.write(f)
        
        # Read the configuration file
        self.config.read(self.config_path)
    
    def get_api_key(self) -> Optional[str]:
        """Get the Stability API Key"""
        try:
            # Prioritize the environment variable if set
            env_key = os.getenv("STABILITY_API_KEY")
            if env_key:
                return env_key
                
            # Get the API key from config.ini
            return self.config.get("stability", "api_key")
        except:
            return None
    
    def set_api_key(self, api_key: str) -> None:
        """Set the Stability API Key"""
        if not self.config.has_section("stability"):
            self.config.add_section("stability")
        
        self.config.set("stability", "api_key", api_key)
        
        with open(self.config_path, "w") as f:
            self.config.write(f)
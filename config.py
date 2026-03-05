""" Loading configuration files """

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings

class ServerConfig(BaseModel):
    url: str

class AuthConfig(BaseModel):
    username: str
    password: str

class Settings(BaseSettings):
    """
    Main Settings class that aggregates sub-configs.
    Pydantic will automatically validate types (e.g., ensuring port is int).
    """
    server: ServerConfig
    auth: AuthConfig

    @classmethod
    def load_from_yaml(cls, path: str = "server_config.yaml"):
        """Load and parse the YAML file into the Pydantic model."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

# Global instance for easy import across test files
config = Settings.load_from_yaml()
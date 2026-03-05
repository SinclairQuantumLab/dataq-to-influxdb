""" Loading configuration files """

import yaml
from pathlib import Path
from pydantic import BaseModel

# ---------------------------------------------------------
# 1. Define Pydantic Models for Validation
# ---------------------------------------------------------

# >>> DI808 logger >>>
class ServerConfig(BaseModel):
    url: str
    event_name: str
    auth: AuthConfig

class AuthConfig(BaseModel):
    username: str
    password: str
# <<< DI808 logger <<<


# >>> InfluxDB >>>

class InfluxDBConfig(BaseModel):
    url: str
    token: str
    org: str
    bucket: str

# <<< InfluxDB <<<


# ---------------------------------------------------------
# 2. Helper function to safely load YAML files
# ---------------------------------------------------------
def load_yaml(file_path: str) -> dict:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

# ---------------------------------------------------------
# 3. Instantiate and Export Settings
# ---------------------------------------------------------
# Load project-specific settings
_server_data = load_yaml("DI808_config.yaml")
server_settings = ServerConfig(**_server_data)

# Load lab-shared settings
_influx_data = load_yaml("influxdb_config.yaml")
influx_settings = InfluxDBConfig(**_influx_data)
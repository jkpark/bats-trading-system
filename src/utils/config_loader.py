import os
import yaml
import logging

def deep_merge(base, override):
    """
    Recursively merges two dictionaries.
    """
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def load_config(base_path="config.yaml", local_path="config.local.yaml"):
    """
    Loads configuration using Chain of Responsibility/Layered approach.
    Priority: config.local.yaml > config.yaml
    """
    config = {}

    # 1. Load base config.yaml
    if os.path.exists(base_path):
        with open(base_path, "r") as f:
            base_config = yaml.safe_load(f) or {}
            config = deep_merge(config, base_config)
    else:
        logging.warning(f"Base config file not found: {base_path}")

    # 2. Load local override config.local.yaml
    if os.path.exists(local_path):
        logging.info(f"Loading local configuration from {local_path}")
        with open(local_path, "r") as f:
            local_config = yaml.safe_load(f) or {}
            config = deep_merge(config, local_config)
    
    if not config:
        logging.error("No configuration loaded.")
        
    return config

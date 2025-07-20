
import streamlit_authenticator as stauth
import yaml
import os
from yaml.loader import SafeLoader

CONFIG_PATH = os.path.join("auth", "config.yaml")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Missing config.yaml for authentication.")
    with open(CONFIG_PATH, 'r') as file:
        return yaml.load(file, Loader=SafeLoader)

def get_authenticator():
    config = load_config()
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )
    return authenticator

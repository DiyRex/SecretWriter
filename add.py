import os
from dotenv import load_dotenv
import requests
import base64
from nacl import encoding, public
import configparser

load_dotenv()

github_token = os.getenv('GITHUB_TOKEN')

def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")

def add_secret(repo, secret_name, secret_value, token):
    # Get the public key for the repository
    url = f"https://api.github.com/repos/{repo}/actions/secrets/public-key"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    public_key = response.json()["key"]
    key_id = response.json()["key_id"]

    # Encrypt the secret
    encrypted_value = encrypt(public_key, secret_value)

    # Add the secret
    url = f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}"
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    response = requests.put(url, json=data, headers=headers)
    return response.status_code == 201 or response.status_code == 204

def add_variable(repo, variable_name, variable_value, token):
    url = f"https://api.github.com/repos/{repo}/actions/variables"
    headers = {"Authorization": f"token {token}"}
    data = {
        "name": variable_name,
        "value": variable_value
    }
    response = requests.post(url, json=data, headers=headers)
    return response.status_code == 201

def read_ini_file(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

# Usage
config = read_ini_file('config.ini')

# Read repository from config
repository = config['general']['repository']

# Process secrets
if 'secrets' in config:
    for secret_name, secret_value in config['secrets'].items():
        if add_secret(repository, secret_name, secret_value, github_token):
            print(f"Secret {secret_name} added successfully")
        else:
            print(f"Failed to add secret {secret_name}")

# Process variables
if 'vars' in config:
    for variable_name, variable_value in config['vars'].items():
        if add_variable(repository, variable_name, variable_value, github_token):
            print(f"Variable {variable_name} added successfully")
        else:
            print(f"Failed to add variable {variable_name}")
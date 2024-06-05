import uuid
import os
from typing import Optional
import hashlib

SECRET_KEY = "TTC-EXP-CALCS"


def get_machine_identifier():
    node_id = uuid.getnode()
    node_id_hex = f"{node_id:X}"
    # with dashes
    return f"{node_id_hex[:4]}-{node_id_hex[4:8]}-{node_id_hex[8:]}"


def get_client_id() -> str:
    machine_identifier = get_machine_identifier()
    return machine_identifier


def hashed_client_id() -> str:
    client_id = get_client_id()
    hashed_id = hashlib.sha512(f'{client_id}{SECRET_KEY}'.encode()).hexdigest()
    return hashed_id


def get_license_key() -> Optional[str]:
    license_file = "license.txt"

    if not os.path.exists(license_file):
        print(f"License file '{license_file}' not found")
        return None

    with open(license_file, "r") as file:
        license_key = file.read().strip()
    print(f"License key: {license_key}")

    return license_key


def check_license() -> bool:
    license_key = get_license_key()
    if license_key is None:
        return False

    hashed_id = hashed_client_id()
    return license_key == hashed_id

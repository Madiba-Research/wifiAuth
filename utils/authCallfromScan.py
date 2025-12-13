from glob import glob
import json
# import os
import requests


# this is same as authenticateCall.py, but do auth call from scanned file stored on the phone

def authenticate_json(user_name, scan_json):
    url = "http://0.0.0.0:5000/authenticate"
    payload = {
        "username": user_name,
        "aps": scan_json
    }
    response = requests.post(url, json=payload)
    print(f'response: {response.json()}')
    return response.json()


def extract_JSON_from_jsonfile(file_path: str) -> list:
    """
    Extract JSON objects from a json file.
    """

    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


if __name__ == "__main__":
    AUTH_DIR = "../authFromPixel7"
    auth_files = glob(f"{AUTH_DIR}/mmoffice_*.json")
    auth_list = []
    for auth_file in auth_files:
        auth_list.append(extract_JSON_from_jsonfile(auth_file))
    for auth in auth_list:
        user = "mmoffice"
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        authenticate_json(user, aps)

    auth_files = glob(f"{AUTH_DIR}/9225_*.json")
    auth_list = []
    for auth_file in auth_files:
        auth_list.append(extract_JSON_from_jsonfile(auth_file))
    for auth in auth_list:
        user = "9225"
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        authenticate_json(user, aps)

    auth_files = glob(f"{AUTH_DIR}/ev1162_*.json")
    auth_list = []
    for auth_file in auth_files:
        auth_list.append(extract_JSON_from_jsonfile(auth_file))
    for auth in auth_list:
        user = "ev1162"
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        authenticate_json(user, aps)
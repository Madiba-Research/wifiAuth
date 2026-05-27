import json
import requests
import os
import re
from glob import glob


def extract_JSON_from_log(file_path: str) -> list:
    """
    Extract JSON objects from a log file.
    """

    json_list = []

    with open(file_path, 'r') as file:
        for log_line in file:
            match = re.search(r'({.*})', log_line)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                # print(data)
                json_list.append(data)
    return json_list


def register_dir(user_name, scan_data_dir):
    url = "http://0.0.0.0:5000/register"
    # user info
    # user_name = "mm1"
    # scan_data_dir = "/Users/noname/mlprojects/mm1data"
    aps = []
    for filename in os.listdir(scan_data_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(scan_data_dir, filename)
            with open(filepath, 'r') as f:
                scan = json.load(f)
                if scan:
                    aps.append(scan)
    payload = {
        "username": user_name,
        "aps": aps
    }

    response = requests.post(url, json=payload)
    print(response.text)


def register_json(user_name, scan_json):
    url = "http://0.0.0.0:5000/register"
    payload = {
        "username": user_name,
        "aps": scan_json
    }
    response = requests.post(url, json=payload)
    print(f'response: {response.json()}')


if __name__ == "__main__":


    # reg for may 2
    REG_DIR = "../log_may2_month"
    reg_files = glob(f"{REG_DIR}/auth_app_reg.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    # manual reg start from here
    for reg in reg_list:
        user_name = reg.get("username")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)


        

        

    

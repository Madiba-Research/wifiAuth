from glob import glob
import json
import os
import re
import requests
import random


def authenticate_file(user_name, file_path):
    url = "http://0.0.0.0:5000/authenticate"
    aps = []

    with open(file_path, 'r') as f:
        scan = json.load(f)
        if scan:
            # randomly get rid of 2 aps
            # scan_dropped = random.sample(scan, len(scan) - 2)
            # scan_diff = [ap for ap in scan if ap not in scan_dropped]
            # print(f'droppend aps: {scan_diff}')
            # aps.append(scan_dropped)

            aps.append(scan)

            payload = {
                "username": user_name,
                "aps": aps
            }

            response = requests.post(url, json=payload)
            print(f'file: {file_path}, response: {response.json()}')


def authenticate_files(user_name, files_dir):
    url = "http://0.0.0.0:5000/authenticate"
    aps = []

    for filename in os.listdir(files_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(files_dir, filename)
            with open(filepath, 'r') as f:
                scan = json.load(f)
                if scan:
                    aps.append(scan)
    payload = {
        "username": user_name,
        "aps": aps
    }

    response = requests.post(url, json=payload)
    print(response.json())


def authenticate_json(user_name, scan_json):
    url = "http://0.0.0.0:5000/authenticate"
    payload = {
        "username": user_name,
        "aps": scan_json
    }
    response = requests.post(url, json=payload)
    print(f'response: {response.json()}')
    return response.json()


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



if __name__ == "__main__":

    AUTH_DIR = "../log_auth_distance_sigma2"
    # normal d1p1 auth first for d5p7
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p7", "d3p7")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        authenticate_json(user, aps)

    # use d1p1, generate d3p1, on model d3
    auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p1")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        authenticate_json(user, aps)
    # p7 & p1 cross testing
    # user d3p1(d1p1) authenticate d5p7
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p7")
        aps = auth["aps"]
        authenticate_json(user, aps)
    # user d3p3 authenticate d3p1
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p7", "d3p1")
        aps = auth["aps"]
        authenticate_json(user, aps)

    
    # for remaining 20 users
    ANOTHER_AUTH_DIR = "../another20loc"
    auth_files = glob(f"{ANOTHER_AUTH_DIR}/*.log")
    reg_auth_list = []
    for auth_file in auth_files:
        reg_auth_list.extend(extract_JSON_from_log(auth_file))
    auth_list = [auth for auth in reg_auth_list if auth["operation"] == "authenticate"]

    user_name_list = ["t" + str(i) for i in range(6, 25)]
    for user_name in user_name_list:
        user_1 = user_name + "p1"
        print("user_1:", user_1)
        user_1_auth = [auth for auth in auth_list if auth["username"] == user_1]
        print(f'user_1_auth count: {len(user_1_auth)}')

        user_7 = user_name + "p7"
        print("user_7:", user_7)
        user_7_auth = [auth for auth in auth_list if auth["username"] == user_7]
        print(f'user_7_auth count: {len(user_7_auth)}')

        # user 7 first, follow above
        for auth in user_7_auth:
            username_7 = user_name + "d3p7"
            aps = auth["aps"]
            response =authenticate_json(username_7, aps)
            print(f'user: {username_7}, auth response: {response}')
        
        # user 1
        for auth in user_1_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            response = authenticate_json(username_1, aps)
            print(f'user: {username_1}, auth response: {response}')

        for auth in user_1_auth:
            username_7 = user_name + "d3p7"
            aps = auth["aps"]
            response = authenticate_json(username_7, aps)
            print(f'user: {username_7}, auth response: {response}')
        for auth in user_7_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            response = authenticate_json(username_1, aps)
            print(f'user: {username_1}, auth response: {response}')
        

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
    
    REG_DIR = "../log_reg_distance"
    reg_files = glob(f"{REG_DIR}/*.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    # manual reg start from here
    # reg for d1
    reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d1p1", "d3p1")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)
        # exit()

    # # reg for d2
    # reg_list_filtered = [item for item in reg_list if "p2" in item.get("username") or "p3" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d1", "d2")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # reg for d3
    # reg_list_filtered = [item for item in reg_list if "p1" in item.get("username") or "p3" in item.get("username")]
    # for reg in reg_list_filtered:
    #     # print(reg.get("username"))
    #     user_name = reg.get("username").replace("d1", "d3").replace("d2", "d3")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # reg for d1
    # reg_list_filtered = [item for item in reg_list if "p3" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d2p3", "d3p3")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)


    # reg_list_filtered = [item for item in reg_list if "p5" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d5p5", "d3p5")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    reg_list_filtered = [item for item in reg_list if "p7" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d5p7", "d3p7")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)


    # reg for another 20 users
    ANOTHER_REG_DIR = "../another20loc"
    reg_files = glob(f"{ANOTHER_REG_DIR}/*.log")
    reg_auth_list = []
    for reg_file in reg_files:
        reg_auth_list.extend(extract_JSON_from_log(reg_file))
    reg_list = [reg for reg in reg_auth_list if reg["operation"] == "register"]
    
    user_list = ["t" + str(i) for i in range(6, 25)]
    # user_list = ["t" + str(i) for i in range(6, 12)]
    for reg in reg_list:
        user_name = reg.get("username")[: -2] + "d3" + reg.get("username")[-2 :]
        # print(f'registering user: {username}')
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)

        

        

    

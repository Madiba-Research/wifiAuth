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

    # user_name = "mm1"
    # user_dir = "/Users/noname/mlprojects/mm2data"
    # authenticate_files(user_name, user_dir)

    # user_name = "mm1"
    # file_path = '/Users/noname/mlprojects/2025-06-19+15:07:25t0.json'
    # # to test if miss some ap
    # authenticate_file(user_name, file_path)


    # user_name = "mm1"
    # files_dir = "/Users/noname/mlprojects/mm2data"
    # for filename in os.listdir(files_dir):
    #     if filename.endswith('.json'):
    #         file_path = os.path.join(files_dir, filename)
    #         authenticate_file(user_name, file_path)
   

    # AUTH_DIR = "../log_auth"
    # auth_files = glob(f"{AUTH_DIR}/*.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # user_list = ["t0", "t1", "t2", "t3", "t4"]
    # for user in user_list:
    #     user_auth_data = [item for item in auth_list if item["username"] == user]
    #     other_users = [u for u in user_list if u != user]
    #     for an_auth in user_auth_data:
    #         for other_user in other_users:
    #             print(f"authenticating {other_user} with {user}'s data")
    #             authenticate_json(other_user, an_auth["aps"])


    # AUTH_DIR = "../log_auth_distance"
    # normal d1p1 auth first
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"]
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)

    # use d2p2, generate d1p2, on model d1
    # auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d2p2", "d1p2")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)
    # # p1 & p2 cross testing
    # # user d1p2(d2p2) authenticate d1p1
    # for auth in auth_list:
    #     user = auth["username"].replace("d2p2", "d1p1")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    # # user d1p1 authenticate d1p2
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d1p2")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    


    # AUTH_DIR = "../log_auth_distance"
    # normal d2p2 auth first
    # auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"]
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)

    # # use d3p3, generate d2p3, on model d2
    # auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d3p3", "d2p3")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)
    # # p2 & p3 cross testing
    # # user d2p3(d3p3) authenticate d2p2
    # for auth in auth_list:
    #     user = auth["username"].replace("d3p3", "d2p2")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    # # user d2p2 authenticate d2p3
    # auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d2p2", "d2p3")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    


    AUTH_DIR = "../log_auth_distance"
    # # normal d3p3 auth first
    # auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"]
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)

    # # use d1p1, generate d3p1, on model d3
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p1")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)
    #     # exit()
    # # p3 & p1 cross testing
    # # user d3p1(d1p1) authenticate d3p3
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p3")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    # # user d3p3 authenticate d3p1
    # auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d3p3", "d3p1")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)


    AUTH_DIR = "../log_auth_distance_sigma2"
    # # # normal d1p1 auth first for d5
    # auth_files = glob(f"{AUTH_DIR}/*_d5p5.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d5p5", "d3p5")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)

    # # use d1p1, generate d3p1, on model d3
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p1")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)
    # # p3 & p1 cross testing
    # # user d3p1(d1p1) authenticate d3p3
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p5")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)
    # # user d3p3 authenticate d3p1
    # auth_files = glob(f"{AUTH_DIR}/*_d5p5.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d5p5", "d3p1")
    #     aps = auth["aps"]
    #     authenticate_json(user, aps)


    AUTH_DIR = "../log_auth_distance_sigma2"
    # # normal d1p1 auth first for d5p7
    # auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d5p7", "d3p7")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     authenticate_json(user, aps)

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


    
    # =========================================
    # plz ignore
    # AUTH_DIR = "../log_auth_wall_sigma2"
    # # cross validation for wall p1 and p3
    # # p1p3p5 is file with true positive logins
    # auth_files = glob(f"{AUTH_DIR}/*_p1p3p5.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # # p1 data on p3
    # for auth in auth_list:
    #     if "p1" in auth["username"]:
    #         user = auth["username"].replace("p1", "p3")
    #         aps = auth["aps"]
    #         authenticate_json(user, aps)
    # # p3 data on p1
    # for auth in auth_list:
    #     if "p3" in auth["username"]:
    #         user = auth["username"].replace("p3", "p1")
    #         aps = auth["aps"]
    #         authenticate_json(user, aps)


    # AUTH_DIR = "../log_auth_wall_sigma2"
    # # cross validation for wall p1 and p5
    # # p1p3p5 is file with true positive logins
    # auth_files = glob(f"{AUTH_DIR}/*_p1p3p5.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # # p1 data on p5
    # for auth in auth_list:
    #     if "p1" in auth["username"]:
    #         user = auth["username"].replace("p1", "p5")
    #         aps = auth["aps"]
    #         authenticate_json(user, aps)
    # # p5 data on p1
    # for auth in auth_list:
    #     if "p5" in auth["username"]:
    #         user = auth["username"].replace("p5", "p1")
    #         aps = auth["aps"]
    #         authenticate_json(user, aps)

    #========================================


    # # auth p7 but with our dummy data
    # AUTH_DIR = "../log_auth_distance_sigma2"
    # # # normal d1p1 auth first for d5p7
    # auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for i in range(-100, -9, 1):
    #     for auth in auth_list:
    #         user = auth["username"].replace("d5p7", "d3p7")
    #         aps = auth["aps"]
    #         for ap_scan in aps:
    #             for ap in ap_scan:
    #                 ap['rssi'] = i
    #         # print(f"authenticating {user} with modified {aps}")
    #         # only take half of ap_scan
    #         aps_half = [random.sample(ap_scan, len(ap_scan)//8) for ap_scan in aps]
    #         # print(f"authenticating {user} with half {aps_half}")
    #         # print(f"authenticating {user} with {aps}")
    #         # authenticate_json(user, aps_half)
    #         # print(f"authenticating {user} with {aps}")
    #         rst = authenticate_json(user, aps)
    #         if rst.get("authenticated") == True:
    #             print("with rssi:", i)
    #     break

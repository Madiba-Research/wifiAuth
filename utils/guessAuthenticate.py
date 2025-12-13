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
    reg_files = glob(f"{REG_DIR}/*_reg7.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    # manual reg start from here
    # reg for d1
    # reg_list_filtered = [item for item in reg_list if "d1" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

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
    # reg_list_filtered = [item for item in reg_list if "d1p1" in item.get("username")]
    
    rssi_set = set()
    ap_count_set = set()

    for reg in reg_list:
        scan_json = reg.get("aps")
        # print(f"scan_json length: {len(scan_json)}")
        for aps in scan_json:
            print(len(aps))
            rssi_list = [ap.get('rssi') for ap in aps]
            rssi_set.update(rssi_list)
            ap_count_set.add(len(aps))
    print(f"Unique RSSI values: {sorted(rssi_set)}")
    min_rssi = min(rssi_set)
    max_rssi = max(rssi_set)
    print(f"RSSI range: {min_rssi} to {max_rssi}")
    print(f"Unique AP counts: {sorted(ap_count_set)}")
    min_ap_count = min(ap_count_set) if ap_count_set else 0
    max_ap_count = max(ap_count_set) if ap_count_set else 0
    print(f"AP count range: {min_ap_count} to {max_ap_count}")


    

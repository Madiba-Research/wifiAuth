import json
import random
import re

import requests


# DROP_RATE = 0.3 # 7% reject
# DROP_RATE = 0.4 # 41% reject
# DROP_RATE = 0.5 # 99% reject
DROP_RATE = 0.55 # 100% reject

def extract_JSON_from_log(file_path: str) -> list:
    json_list = []

    with open(file_path, "r") as file:
        for log_line in file:
            match = re.search(r"({.*})", log_line)
            if match:
                json_list.append(json.loads(match.group(1)))

    return json_list


def authenticate_json(user_name, scan_json):
    url = "http://0.0.0.0:5000/authenticate"
    payload = {
        "username": user_name,
        "aps": scan_json,
    }
    response = requests.post(url, json=payload)
    print(f"response: {response.json()}")
    return response.json()


if __name__ == "__main__":
    auth_list = extract_JSON_from_log("../log_may2_month/auth_app_week1.log")

    first_auth = None
    for auth in auth_list:
        if auth.get("operation") == "authenticate" and auth.get("username") == "t0":
            first_auth = auth
            break

    if first_auth is None:
        raise ValueError("No t0 authenticate record found")

    false_count = 0
    for _ in range(100):
        all_bssids = set()
        for scan in first_auth["aps"]:
            for ap in scan:
                all_bssids.add(ap["bssid"])

        drop_num = int(len(all_bssids) * DROP_RATE)
        drop_bssids = set(random.sample(list(all_bssids), drop_num))

        aps = []
        for scan in first_auth["aps"]:
            # drop_num = int(len(scan) * DROP_RATE)
            # keep_num = len(scan) - drop_num
            # aps.append(random.sample(scan, keep_num))
            aps.append([ap for ap in scan if ap["bssid"] not in drop_bssids])

        response = authenticate_json(first_auth["username"], aps)
        if response.get("authenticated") is False:
            false_count += 1

    print(f"false count: {false_count}")

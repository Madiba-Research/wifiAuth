import json
import re

import requests


def extract_JSON_from_log(file_path: str) -> list:
    json_list = []

    with open(file_path, "r") as file:
        for log_line in file:
            match = re.search(r"({.*})", log_line)
            if match:
                json_list.append(json.loads(match.group(1)))

    return json_list


def register_json(user_name, scan_json):
    url = "http://0.0.0.0:5000/register"
    payload = {
        "username": user_name,
        "aps": scan_json,
    }
    response = requests.post(url, json=payload)
    print(f"response: {response.json()}")


if __name__ == "__main__":
    auth_list = extract_JSON_from_log("../log_may2_month/auth_app_week2.log")

    scans = []
    for auth in auth_list:
        if auth.get("operation") == "authenticate" and auth.get("username") == "t4":
            scans.extend(auth["aps"])

    print(f"register t5 with {len(scans)} t4 scans from week2")
    register_json("t5", scans)

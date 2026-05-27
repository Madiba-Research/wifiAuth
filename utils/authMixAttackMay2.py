import json
import random
import re

import requests


MIX_RATES = [i / 10 for i in range(1, 11)]
ATTACKER_LOC = "t0"
TARGET_LOCS = ["t1", "t2", "t3", "t5"]
REPEAT = 10


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
    auth_list = extract_JSON_from_log("../log_may2_month/auth_app_week2.log")
    attacker_auths = [
        auth for auth in auth_list
        if auth.get("operation") == "authenticate" and auth.get("username") == ATTACKER_LOC
    ]

    if not attacker_auths:
        raise ValueError("No attacker authenticate record found")

    ratio_false_counts = {mix_rate: 0 for mix_rate in MIX_RATES}
    ratio_total_counts = {mix_rate: 0 for mix_rate in MIX_RATES}
    ratio_true_counts_by_target = {
        mix_rate: {target_loc: 0 for target_loc in TARGET_LOCS}
        for mix_rate in MIX_RATES
    }

    for target_loc in TARGET_LOCS:
        target_auths = [
            auth for auth in auth_list
            if auth.get("operation") == "authenticate" and auth.get("username") == target_loc
        ]
        if not target_auths:
            raise ValueError(f"No target authenticate record found for {target_loc}")

        for mix_rate in MIX_RATES:
            false_count = 0
            print(f"target: {target_loc}, mix rate: {mix_rate}")
            for attacker_auth, target_auth in zip(attacker_auths, target_auths):
                for _ in range(REPEAT):
                    mixed_aps = []
                    for attacker_scan, target_scan in zip(attacker_auth["aps"], target_auth["aps"]):
                        fake_num = int(len(target_scan) * mix_rate)
                        mixed_aps.append(attacker_scan + random.sample(target_scan, fake_num))

                    response = authenticate_json(target_loc, mixed_aps)
                    ratio_total_counts[mix_rate] += 1
                    if response.get("authenticated") is False:
                        false_count += 1
                        ratio_false_counts[mix_rate] += 1
                    else:
                        ratio_true_counts_by_target[mix_rate][target_loc] += 1

            print(f"false count: {false_count}")

    print("combined results by mix rate")
    for mix_rate in MIX_RATES:
        true_counts = ", ".join(
            f"{target_loc}={ratio_true_counts_by_target[mix_rate][target_loc]}"
            for target_loc in TARGET_LOCS
        )
        print(f"mix rate: {mix_rate}, false count: {ratio_false_counts[mix_rate]}/{ratio_total_counts[mix_rate]}, true counts: {true_counts}")

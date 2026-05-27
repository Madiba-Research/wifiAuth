from glob import glob
import json
import math
import re
from collections import defaultdict


DATA_DIR = "./another20loc"
MISSING_RSSI = -100.0
REG_SCAN_COUNT = 60

EXCLUDED_USERS = {"t6", "t7", "t11", "t12", "t21"}
EVAL_USERS = {"t8", "t9", "t10", "t13", "t15"}
TEST_USERS = {"t14", "t16", "t17", "t18", "t19", "t20", "t22", "t23", "t24"}


def extract_json_from_log(file_path: str) -> list:
    json_list = []
    with open(file_path, "r") as file:
        for log_line in file:
            match = re.search(r"({.*})", log_line)
            if match:
                json_list.append(json.loads(match.group(1)))
    return json_list


def load_records(data_dir: str) -> list:
    records = []
    for log_file in glob(f"{data_dir}/*.log"):
        records.extend(extract_json_from_log(log_file))
    return records


def mean_rssi_profile(scan_list: list, expected_scan_count: int | None = None) -> dict:
    scan_count = expected_scan_count if expected_scan_count is not None else len(scan_list)
    if scan_count <= 0:
        return {}

    rssi_by_bssid = defaultdict(list)
    for scan in scan_list:
        for ap in scan:
            rssi_by_bssid[ap["bssid"]].append(float(ap["rssi"]))

    profile = {}
    for bssid, values in rssi_by_bssid.items():
        missing_count = max(scan_count - len(values), 0)
        profile[bssid] = (sum(values) + missing_count * MISSING_RSSI) / scan_count
    return profile


def mse_distance(reg_profile: dict, auth_profile: dict) -> float:
    bssids = set(reg_profile) | set(auth_profile)
    if not bssids:
        return math.inf

    squared_error = 0.0
    for bssid in bssids:
        reg_rssi = reg_profile.get(bssid, MISSING_RSSI)
        auth_rssi = auth_profile.get(bssid, MISSING_RSSI)
        squared_error += (auth_rssi - reg_rssi) ** 2
    return squared_error / len(bssids)


def build_register_profiles(register_records: list) -> dict:
    profiles = {}
    for record in register_records:
        username = record["username"]
        profiles[username] = mean_rssi_profile(record["aps"], expected_scan_count=REG_SCAN_COUNT)
    return profiles


def group_auth_records(auth_records: list) -> dict:
    grouped = defaultdict(list)
    for record in auth_records:
        grouped[record["username"]].append(record)
    return grouped


def user_id(username: str) -> str:
    match = re.match(r"(t\d+)", username)
    if not match:
        raise ValueError(f"Cannot parse user id from username: {username}")
    return match.group(1)


def collect_scores(users: set, reg_profiles: dict, auth_by_username: dict) -> tuple[list, list]:
    genuine_scores = []
    impostor_scores = []

    for user in sorted(users, key=lambda item: int(item[1:])):
        if user in EXCLUDED_USERS:
            continue

        p1_reg = reg_profiles.get(f"{user}p1")
        p7_reg = reg_profiles.get(f"{user}p7")
        if p1_reg is None or p7_reg is None:
            print(f"Skipping {user}: missing register data")
            continue

        for auth_record in auth_by_username.get(f"{user}p1", []):
            auth_profile = mean_rssi_profile(auth_record["aps"])
            genuine_scores.append(mse_distance(p1_reg, auth_profile))

        for auth_record in auth_by_username.get(f"{user}p7", []):
            auth_profile = mean_rssi_profile(auth_record["aps"])
            genuine_scores.append(mse_distance(p7_reg, auth_profile))
            impostor_scores.append(mse_distance(p1_reg, auth_profile))

    return genuine_scores, impostor_scores


def metrics_at_threshold(genuine_scores: list, impostor_scores: list, threshold: float) -> dict:
    false_rejects = sum(score > threshold for score in genuine_scores)
    false_accepts = sum(score <= threshold for score in impostor_scores)

    genuine_total = len(genuine_scores)
    impostor_total = len(impostor_scores)

    frr = false_rejects / genuine_total if genuine_total else 0.0
    far = false_accepts / impostor_total if impostor_total else 0.0
    tar = 1.0 - frr
    true_accepts = genuine_total - false_rejects
    true_rejects = impostor_total - false_accepts
    precision = true_accepts / (true_accepts + false_accepts) if true_accepts + false_accepts else 0.0
    f1 = (
        2 * precision * tar / (precision + tar)
        if precision + tar
        else 0.0
    )
    accuracy = (
        (true_accepts + true_rejects)
        / (genuine_total + impostor_total)
        if genuine_total + impostor_total
        else 0.0
    )

    return {
        "threshold": threshold,
        "tar": tar,
        "frr": frr,
        "far": far,
        "precision": precision,
        "f1": f1,
        "accuracy": accuracy,
        "false_rejects": false_rejects,
        "false_accepts": false_accepts,
        "genuine_total": genuine_total,
        "impostor_total": impostor_total,
    }


def find_eer_threshold(genuine_scores: list, impostor_scores: list) -> dict:
    all_scores = sorted(set(genuine_scores + impostor_scores))
    if not all_scores:
        raise ValueError("No eval scores available for threshold search")

    epsilon = 1e-9
    candidates = [all_scores[0] - epsilon] + all_scores + [all_scores[-1] + epsilon]
    best = None

    for threshold in candidates:
        metrics = metrics_at_threshold(genuine_scores, impostor_scores, threshold)
        key = (abs(metrics["frr"] - metrics["far"]), -metrics["accuracy"], metrics["threshold"])
        if best is None or key < best[0]:
            best = (key, metrics)

    return best[1]


def find_eval_threshold(genuine_scores: list, impostor_scores: list) -> dict:
    max_genuine = max(genuine_scores)
    min_impostor = min(impostor_scores)
    if max_genuine < min_impostor:
        return metrics_at_threshold(
            genuine_scores,
            impostor_scores,
            (max_genuine + min_impostor) / 2,
        )
    return find_eer_threshold(genuine_scores, impostor_scores)


def print_metrics(title: str, metrics: dict) -> None:
    print(title)
    print(f"  threshold: {metrics['threshold']:.6f}")
    print(f"  TAR: {metrics['tar'] * 100:.2f}%")
    print(f"  FRR: {metrics['frr'] * 100:.2f}% ({metrics['false_rejects']}/{metrics['genuine_total']})")
    print(f"  FAR: {metrics['far'] * 100:.2f}% ({metrics['false_accepts']}/{metrics['impostor_total']})")
    print(f"  precision: {metrics['precision'] * 100:.2f}%")
    print(f"  F1: {metrics['f1'] * 100:.2f}%")
    print(f"  accuracy: {metrics['accuracy'] * 100:.2f}%")


def main() -> None:
    records = load_records(DATA_DIR)
    register_records = [record for record in records if record.get("operation") == "register"]
    auth_records = [record for record in records if record.get("operation") == "authenticate"]

    reg_profiles = build_register_profiles(register_records)
    auth_by_username = group_auth_records(auth_records)

    eval_genuine, eval_impostor = collect_scores(EVAL_USERS, reg_profiles, auth_by_username)
    eval_metrics = find_eer_threshold(eval_genuine, eval_impostor)

    test_genuine, test_impostor = collect_scores(TEST_USERS, reg_profiles, auth_by_username)
    test_metrics = metrics_at_threshold(test_genuine, test_impostor, eval_metrics["threshold"])

    print(f"Data directory: {DATA_DIR}")
    print(f"Excluded users: {', '.join(sorted(EXCLUDED_USERS, key=lambda item: int(item[1:])))}")
    print(f"Eval users: {', '.join(sorted(EVAL_USERS, key=lambda item: int(item[1:])))}")
    print(f"Test users: {', '.join(sorted(TEST_USERS, key=lambda item: int(item[1:])))}")
    print()
    print_metrics("Eval threshold search result:", eval_metrics)
    print()
    print_metrics("Final test result:", test_metrics)


if __name__ == "__main__":
    main()

import json


def load_json_from_file(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def sort_json_with_bssid(json_data):
    return sorted(json_data, key=lambda x: x['bssid'])


if __name__ == "__main__":
    # file_path = '2025-06-28+17:14:07ev10177p1.json'
    # file_path = "2025-06-28+17:14:10ev10177p1.json"
    # file_path = "2025-06-28+17:16:04ev10177p3.json"
    file_path = "2025-06-28+17:16:06ev10177p3.json"
    json_data = load_json_from_file(file_path)
    sorted_data = sort_json_with_bssid(json_data)
    for entry in sorted_data:
        print(entry)

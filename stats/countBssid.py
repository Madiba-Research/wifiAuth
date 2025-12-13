import json
import os

g_max_rssi = -100
g_min_rssi = 0


def extract_bssids(data):
    global g_max_rssi, g_min_rssi
    bssids_raw = [entry['bssid'] for entry in data]
    rssis = [entry['rssi'] for entry in data]
    max_rssi = max(rssis)
    min_rssi = min(rssis)
    # print(f"Max RSSI: {max_rssi}, Min RSSI: {min_rssi}")
    if max_rssi > g_max_rssi:
        g_max_rssi = max_rssi
    if min_rssi < g_min_rssi:
        g_min_rssi = min_rssi
    return bssids_raw


def count_bssid_from_dir(directory):

    bssid_set = set()
    bssid_number = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data:
                    bssids = extract_bssids(data)
                    bssid_set.update(bssids)
                    bssid_number.append(len(bssids))
    print(f"Total unique BSSIDs: {len(bssid_set)}")
    print(f"Average number of BSSIDs per file: {sum(bssid_number)/len(bssid_number)}")
    print(f"Max number of BSSIDs in a file: {max(bssid_number)}")
    print(f"Min number of BSSIDs in a file: {min(bssid_number)}")


def count_bssid_of_location_from_dir(directory):

    location_dict = dict()
    
    for filename in os.listdir(directory):
        if not filename.endswith('.json'):
            continue
        file_location = filename[19:-4]
        # count location scans:
        file_path = os.path.join(directory, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            if data:
                bssids = extract_bssids(data)
                if file_location not in location_dict:
                    location_dict[file_location] = list()
                location_dict[file_location].append(len(bssids))

    location_avg = {}
    for location, bssid_counts in location_dict.items():
        location_avg[location] = sum(bssid_counts) / len(bssid_counts)
    sorted_locations = sorted(location_avg.items(), key=lambda x: x[1], reverse=True)


    for i, (location, avg_count) in enumerate(sorted_locations[:3], 1):
        print(f"{i}. {location}: {avg_count:.2f} (扫描次数: {len(location_dict[location])})")
        variance = sum((x - avg_count) ** 2 for x in location_dict[location]) / len(location_dict[location])
        print(f"{i}. {location}: {avg_count:.2f} (扫描次数: {len(location_dict[location])}, 方差: {variance:.2f})")

    
    print(f"\n平均 BSSID 数量最少的后三个地点:")
    for i, (location, avg_count) in enumerate(sorted_locations[-3:], 1):
        print(f"{i}. {location}: {avg_count:.2f} (扫描次数: {len(location_dict[location])})")
        variance = sum((x - avg_count) ** 2 for x in location_dict[location]) / len(location_dict[location])
        print(f"{i}. {location}: {avg_count:.2f} (扫描次数: {len(location_dict[location])}, 方差: {variance:.2f})")
    


if __name__ == "__main__":
    # directory = '../data630'
    # count_bssid_from_dir(directory)
    # print(f"Global Max RSSI: {g_max_rssi}, Global Min RSSI: {g_min_rssi}")
    # print("-----")

    # g_max_rssi = -100
    # g_min_rssi = 0
    # directory = '../data630d1'
    # count_bssid_from_dir(directory)
    # print(f"Global Max RSSI: {g_max_rssi}, Global Min RSSI: {g_min_rssi}")
    # print("-----")

    # g_max_rssi = -100
    # g_min_rssi = 0
    # directory = '../data630d2'
    # count_bssid_from_dir(directory)
    # print(f"Global Max RSSI: {g_max_rssi}, Global Min RSSI: {g_min_rssi}")
    # print("-----")

    # g_max_rssi = -100
    # g_min_rssi = 0
    # directory = '../data630d3'
    # count_bssid_from_dir(directory)
    # print(f"Global Max RSSI: {g_max_rssi}, Global Min RSSI: {g_min_rssi}")

    g_max_rssi = -100
    g_min_rssi = 0
    directory = '../data630d1'
    count_bssid_of_location_from_dir(directory)

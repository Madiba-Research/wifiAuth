import json
import requests
import os


if __name__ == "__main__":
    url = "http://0.0.0.0:5000/simregister"
    # user info
    user_name = "username"
    scan_data_dir = "/Users/noname/mlprojects/wifiOneLoc"
    aps = []
    for filename in os.listdir(scan_data_dir):
        if filename.endswith('ev09189p1.json'):
            filepath = os.path.join(scan_data_dir, filename)
            with open(filepath, 'r') as f:
                scan = json.load(f)
                if scan:
                    aps.append(scan)
    print(f"Number of scans: {len(aps)}")

    # payload = {
    #     "username": user_name,
    #     "aps": aps
    # }

    # response = requests.post(url, json=payload)
    # print(response.text)


    ## To test the change of mean with number of scan increase
    # for i in range(len(aps)):
    #     sub_aps = aps[:i + 3]  # 从第一个到第 i 个（包含）
    #     payload = {
    #         "username": user_name,
    #         "aps": sub_aps
    #     }

    #     response = requests.post(url, json=payload)
    #     print(response.text)

    # To test the distribution of these scans
    # If, for each dimension, the distribution is normal.
    for ap in aps:
        payload = {
            "username": user_name,
            "aps": [ap]  # 只发送一个扫描数据
        }

        response = requests.post(url, json=payload)
        print(response.text)

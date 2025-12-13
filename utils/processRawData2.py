import os
import json
import torch
from torch_geometric.data import Data


# this is same process of dataset, but, it has the categories.json file saved, as dict of index - location pair

def process_json_files(directory, processed_directory):
    graphs = []
    categories = dict()
    cat_idx = 0

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            cat = filename[19:].split('.')[0]
            if cat not in categories:
                categories[cat] = cat_idx
                cat_idx += 1
            # print(cat)
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data:
                    graphs.append(create_pyg_graph(data, categories[cat]))
        # break

    for i, graph in enumerate(graphs):
        torch.save(graph, os.path.join(processed_directory, f'data_{i+1}.pt'))
    
    with open('categories.json', 'w') as f:
        json.dump(categories, f, indent=4)


def mac_to_feature(mac: str) -> list:
    # 移除冒号并提取前 6 个字节
    clean_mac = mac.replace(":", "")[:12]
    # 每两个字符转换为一个整数（0-255）
    return [int(clean_mac[i:i+2], 16) for i in range(0, 12, 2)]

def create_pyg_graph(data, cat):
    # Assuming data is a list of dictionaries with 'bssid' and 'rssi' keys
    bssids_raw = [entry['bssid'] for entry in data]
    # print(bssids_raw)
    bssids = [mac_to_feature(bssid_raw) for bssid_raw in bssids_raw]
    # print(bssids)
    rssis = [entry['rssi'] for entry in data]
    rssis_normalized = [(rssi + 100) / 100.0 for rssi in rssis]  # Normalize RSSI to [0, 1]

    # Create nodes
    node_features = torch.tensor([[0, 0, 0, 0, 0, 0]] + bssids, dtype=torch.float)
    num_nodes = len(node_features)

    # Create edges
    edge_index = torch.tensor([[0] * len(bssids), list(range(1, num_nodes))], dtype=torch.long)
    # edge_attr = torch.tensor(rssis, dtype=torch.float).view(-1, 1)
    edge_attr = torch.tensor(rssis_normalized, dtype=torch.float).view(-1, 1)

    # Create PyG graph
    graph = Data(x=node_features, edge_index=edge_index, edge_attr=edge_attr, y=cat)
    
    return graph

if __name__ == "__main__":
    # raw data directory
    # directory = '../data630d2'
    directory = '../data630d3'
    # directory = '../datamm'

    # processed_directory = '../data630d2processed'
    # processed_directory = '../data630d3processednorm'

    # norm2 has label y that is string instead of integer
    processed_directory = '../data630d3processednormDict'

    # if processed_directory not in os.listdir():
    #     os.mkdir(processed_directory)
    process_json_files(directory, processed_directory)
    # for graph in graphs:
    #     print(graph)
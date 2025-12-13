# load the trained model but only the encoder part
# then encode the test data graph

import json
import torch
from models.Encoderfuzzy import TripletNet, GNNEncoder
from utils.ProcessRawData import create_pyg_graph

def process_json_file(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
        if not data:
            return None
        return create_pyg_graph(data, None)
    

device = 'cpu'
encoder_model = GNNEncoder(input_dim=6, hidden_dim=16, output_dim=8).to(device)
triplet_model = TripletNet(encoder_model).to(device)
checkpoint = torch.load('better_best_model.pth', map_location=device)

print("\n=== Checkpoint Contents ===")
print(f"Epoch: {checkpoint['epoch']}")
print(f"Loss: {checkpoint['loss']:.4f}")
print(f"Accuracy: {checkpoint['accuracy']:.4f}")

triplet_model.load_state_dict(checkpoint['model_state_dict'])
encoder_model.eval()
with torch.no_grad():
    # graph_1 = process_json_file('/Users/noname/mlprojects/gnn_demo/betterdata/2025-06-15+13:34:31seatright.json')
    # graph_1 = process_json_file('/Users/noname/mlprojects/gnn_demo/betterdata/2025-06-15+13:35:01seatright.json')
    graph_1 = process_json_file('/Users/noname/mlprojects/gnn_demo/betterdata/2025-06-16+10:52:31lounge.json')

    # output_1 = encoder_model(graph_1)
    # print(f"Encoded graph 1: {output_1}")
    x = graph_1.x.to(device)
    edge_index = graph_1.edge_index.to(device)
    if hasattr(graph_1, 'batch') and graph_1.batch is not None:
        batch = graph_1.batch.to(device)
    else:
        batch = torch.zeros(graph_1.num_nodes, dtype=torch.long).to(device)

    output_1 = encoder_model(x, edge_index, batch)
    print(f"Encoded graph 1: {output_1}")
    

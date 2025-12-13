import json
import torch
from models.Encoderdemo import SiameseGNN
from utils.ProcessRawData import create_pyg_graph

def process_json_file(file_name):
    with open(file_name, 'r') as f:
        data = json.load(f)
        return create_pyg_graph(data, None)


device = 'cpu'
loaded_model = SiameseGNN(input_dim=6, hidden_dim=64, output_dim=64).to(device)
checkpoint = torch.load('best_model.pth', map_location=device)
# Print all stored information
print("\n=== Checkpoint Contents ===")
print(f"Epoch: {checkpoint['epoch']}")
print(f"Loss: {checkpoint['loss']:.4f}")
print(f"Accuracy: {checkpoint['accuracy']:.4f}")


loaded_model.load_state_dict(checkpoint['model_state_dict'])
loaded_model.eval()

# prepare inputs
raw_eval_directory = './test_data'
graph_1 = process_json_file(f'{raw_eval_directory}/2025-03-09+16:22:28garbage.json')
graph_2 = process_json_file(f'{raw_eval_directory}/2025-03-08+13:01:38seat.json')

with torch.no_grad():
    output = loaded_model(graph_1, graph_2)

# TODO: add a sigmoid or similar activation to limit the output to [0, 1] 
print(f"Prediction: {output}")
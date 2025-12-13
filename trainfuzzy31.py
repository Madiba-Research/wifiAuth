from collections import defaultdict
import os
import random
import torch
# from torch_geometric.datasets import TUDataset
from torch_geometric.loader import DataLoader
from torch_geometric.data import Batch
# from models.Encoderfuzzy import TripletNet, GNNEncoder
from models.Encoderfuzzy31 import TripletNet, GNNEncoder

import matplotlib.pyplot as plt
import json


# this is the model training we will use for nerual fuzzy extractor
# different from trainfuzzy.py, this allows more hard negative mining (hnm) data in the training set

def generate_valid_triplets(dataset):
    class_dict = defaultdict(list)

    cat_dict = dict()

    with open('categories.json', 'r') as f:
        cat_dict = json.load(f)
    reverse_cat_dict = {v: k for k, v in cat_dict.items()}

    for data in dataset:
        class_dict[data.y].append(data)
    triplets = []
    for cls, graphs in class_dict.items():
        cls_name = reverse_cat_dict[cls]
        for i in range(len(graphs)):
            graph_a = graphs[i]
            for j in range(i + 1, len(graphs)):
                graph_p = graphs[j]

                hn_cls = None 

                # this is old shit, we discard
                # # pick a random class not current cls from class_dict
                # another_cls = random.choice(list(set(class_dict.keys()) - {cls}))
                # graph_n = random.choice(class_dict[another_cls])
                # # print(f'cls: {cls}, another_cls: {another_cls}')

                # make graph_n with hard negative mining
                if cls_name.endswith("p1"):
                    hn_cls_name = cls_name.replace("p1", "p3")
                    hn_cls = cat_dict[hn_cls_name]
                    hard_graph_n = random.choice(class_dict[hn_cls])
                elif cls_name.endswith("p3"):
                    hn_cls_name = cls_name.replace("p3", "p1")
                    hn_cls = cat_dict[hn_cls_name]
                    hard_graph_n = random.choice(class_dict[hn_cls])
                triplets.append((graph_a, graph_p, hard_graph_n))

                # if hn_cls is None:
                #     print(f'hn_cls is None for cls_name: {cls_name}')

                # make graph_n with easy negative
                another_cls = random.choice(list(set(class_dict.keys()) - {cls} - {hn_cls}))
                graph_n = random.choice(class_dict[another_cls])
                triplets.append((graph_a, graph_p, graph_n))
    return triplets


# data_dir = './better_processed_data'
# data_dir = './data630d3processed'
# model_file_name = 'best_630d3_model.pth'
# loss_img_name = 'loss_curve_d3.png'
data_dir = './data630d3processednormDict'
model_file_name = 'best_630d3norm_hnm_model3_mixpool_res_a2.pth'
loss_img_name = 'loss_curve_d3norm_hnm3_mixpool_res_a2.png'

data_files = [f for f in os.listdir(data_dir) if f.endswith('.pt')]
dataset = [torch.load(os.path.join(data_dir, f), weights_only=False) for f in data_files]
transformed_dataset = generate_valid_triplets(dataset)

# exit(0)

train_ratio = 0.8
train_dataset = transformed_dataset[:int(train_ratio * len(transformed_dataset))]
test_dataset = transformed_dataset[int(train_ratio * len(transformed_dataset)):]

train_loader = DataLoader(train_dataset, batch_size=5, shuffle=True, follow_batch=['x'])
test_loader = DataLoader(test_dataset, batch_size=5, shuffle=False)

# Build the model, only use CPU as MPS is not supported for PyG
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
device = torch.device("cpu")
print(f'Using device: {device}')
# encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=64).to(device)
# encoder_model = GNNEncoder(input_dim=6, hidden_dim=16, output_dim=8).to(device)
encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=32).to(device)
# encoder_model = GNNEncoderCP(input_dim=6, hidden_dim=64, output_dim=64).to(device)
model = TripletNet(encoder_model).to(device)

# optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
# optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
# scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=3)
# criterion = torch.nn.BCEWithLogitsLoss()
# criterion = torch.nn.TripletMarginLoss(margin=4.0, p=2)  # Triplet loss with margin
criterion = torch.nn.TripletMarginLoss(margin=2.0, p=2)  # Triplet loss with margin
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=7)

def train():
    model.train()
    total_loss = 0
    for data in train_loader:  # Iterate in batches over the training dataset.
        optimizer.zero_grad()  # Clear gradients.
        g1, g2, g3 = data
        g1 = g1.to(device)
        g2 = g2.to(device)
        g3 = g3.to(device)
        # out = model(g1, g2, g3).squeeze()  # Perform a single forward pass.
        out = model(g1, g2, g3)
        # print(out)
        loss_outputs = criterion(*out)  # Compute the loss.
        loss = loss_outputs[0] if type(loss_outputs) in (tuple, list) else loss_outputs
        total_loss += loss.item()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
         
    return total_loss / len(train_loader)

def test():
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for data in test_loader:
            g1, g2, g3 = data
            g1, g2, g3 = g1.to(device), g2.to(device), g3.to(device)
            outputs = model(g1, g2, g3)
            if type(outputs) not in (tuple, list):
                outputs = (outputs,)
            loss_outputs = criterion(*outputs)
            loss = loss_outputs[0] if type(loss_outputs) in (tuple, list) else loss_outputs
            val_loss += loss.item()
    return val_loss / len(test_loader)

best_test_loss = float('inf')

train_losses = []
test_losses = []

# for epoch in range(1, 150):
for epoch in range(1, 120):
    train_loss = train()
    test_loss = test()

    train_losses.append(train_loss)
    test_losses.append(test_loss)

    if test_loss < best_test_loss:
        # best_test_acc = test_loss
        best_test_loss = test_loss
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': train_loss,
            'accuracy': test_loss,
        }, model_file_name)  # Save to current directory

    scheduler.step(test_loss)

    if epoch % 5 == 0:
        print(f'Epoch: {epoch:03d}, Train loss: {train_loss:.4f}, Test loss: {test_loss:.4f}')

plt.figure(figsize=(10, 6))
plt.plot(train_losses, label='Train Loss')
plt.plot(test_losses, label='Test Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Train and Test Loss over Epochs')
plt.legend()
plt.grid(True)
plt.savefig(loss_img_name)  # 可选：保存图像
plt.show()

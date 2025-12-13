from collections import defaultdict
import os
import random
import torch
from torch.utils.data import Dataset, DataLoader
# from torch_geometric.datasets import TUDataset
# from torch_geometric.loader import DataLoader
# from torch_geometric.data import Batch
# from models.Encoderfuzzy import TripletNet, GNNEncoder
# from models.Encoderfuzzy3 import TripletNet, GNNEncoder
from models.FingerprintModel import TripletNet, CNNENcoder
import numpy as np

import matplotlib.pyplot as plt
import json
import random


# this is the model training we will use for nerual fuzzy extractor
# different from trainfuzzy.py, this allows more hard negative mining (hnm) data in the training set

# we came up with our new model, with only take rssi as fingerprints


def generate_valid_triplets(features, labels, data_dir):
    class_dict = defaultdict(list)

    cat_dict = dict()

    with open(os.path.join(data_dir, 'categories.json'), 'r') as f:
        cat_dict = json.load(f)
    reverse_cat_dict = {v: k for k, v in cat_dict.items()}

    # for data in dataset:
    #     class_dict[data.y].append(data)

    for i in range(len(labels)):
        class_dict[labels[i]].append(i)

    triplets = []
    for cls, indices in class_dict.items():
        cls_name = reverse_cat_dict[cls]
        for i in range(len(indices)):
            graph_a = indices[i]
            for j in range(i + 1, len(indices)):
                graph_p = indices[j]

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


def triplet_collate_fn(batch):
    features_a = torch.stack([item[0] for item in batch])
    features_p = torch.stack([item[1] for item in batch])
    features_n = torch.stack([item[2] for item in batch])
    return features_a, features_p, features_n

class TripletDataset(Dataset):
    def __init__(self, triplets, features):
        self.triplets = triplets
        self.features = features
    
    def __len__(self):
        return len(self.triplets)
    
    def __getitem__(self, idx):
        idx_a, idx_p, idx_n = self.triplets[idx]
        # print("Triplet indices:")
        # print(self.features[idx_a])
        # print(self.features[idx_p])
        # print(self.features[idx_n])
        return self.features[idx_a], self.features[idx_p], self.features[idx_n]



# data_dir = './better_processed_data'
# data_dir = './data630d3processed'
# model_file_name = 'best_630d3_model.pth'
# loss_img_name = 'loss_curve_d3.png'
data_dir = './data630d3processedFingerprint'
model_file_name = 'best_630d3fingerprintCNN.pth'
loss_img_name = 'loss_curve_d3fingerprintCNN.png'

# data_files = [f for f in os.listdir(data_dir) if f.endswith('.pt')]
# dataset = [torch.load(os.path.join(data_dir, f), weights_only=False) for f in data_files]
np_data = np.load(os.path.join(data_dir, 'fingerprints.npz'))
features = np_data['features']
labels = np_data['labels']

triplet_idx_dataset = generate_valid_triplets(features, labels, data_dir)

# exit(0)

random.shuffle(triplet_idx_dataset)

train_ratio = 0.8
# train_dataset = transformed_dataset[:int(train_ratio * len(transformed_dataset))]
# test_dataset = transformed_dataset[int(train_ratio * len(transformed_dataset)):]

# train_loader = DataLoader(train_dataset, batch_size=5, shuffle=True, follow_batch=['x'])
# test_loader = DataLoader(test_dataset, batch_size=5, shuffle=False)

split_idx = int(train_ratio * len(triplet_idx_dataset))
train_triplets = triplet_idx_dataset[:split_idx]
test_triplets = triplet_idx_dataset[split_idx:]

features_tensor = torch.tensor(features, dtype=torch.float)
train_dataset = TripletDataset(train_triplets, features_tensor)
test_dataset = TripletDataset(test_triplets, features_tensor)

# # Build the model, only use CPU as MPS is not supported for PyG
# # device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
# device = torch.device("cpu")
# print(f'Using device: {device}')
# # encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=64).to(device)
# # encoder_model = GNNEncoder(input_dim=6, hidden_dim=16, output_dim=8).to(device)
# encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=32).to(device)
# # encoder_model = GNNEncoderCP(input_dim=6, hidden_dim=64, output_dim=64).to(device)
# model = TripletNet(encoder_model).to(device)

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
# device = torch.device("cpu")
# encoder_model = WiFiHistogramEncoder(input_dim=100, embed_dim=32).to(device)
# encoder_model = MLPEncoder(input_dim=100, embed_dim=32).to(device)
encoder_model = CNNENcoder(input_dim=100, embed_dim=32).to(device)
model = TripletNet(encoder_model).to(device)


train_loader = DataLoader(train_dataset, batch_size=20, shuffle=True, collate_fn=triplet_collate_fn)
test_loader = DataLoader(test_dataset, batch_size=20, shuffle=False, collate_fn=triplet_collate_fn)

# device = torch.device("cpu")
print(f'Using device: {device}')

# optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
# optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
# scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=3)
# criterion = torch.nn.BCEWithLogitsLoss()
# criterion = torch.nn.TripletMarginLoss(margin=4.0, p=2)  # Triplet loss with margin
criterion = torch.nn.TripletMarginLoss(margin=3.0, p=2)  # Triplet loss with margin
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

for epoch in range(1, 100):
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

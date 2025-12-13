from collections import defaultdict
import os
import random
import torch
# from torch_geometric.datasets import TUDataset
from torch_geometric.loader import DataLoader
from torch_geometric.data import Batch
# from models.Encoderfuzzy import TripletNet, GNNEncoder
# from models.Encoderfuzzy3 import TripletNet, GNNEncoder
from models.Encoderfuzzy3 import AuthSenseSiemase, GNNEncoder

import matplotlib.pyplot as plt
import json

from torch.utils.data import Dataset as TorchDataset
from torch.utils.data import DataLoader as TorchDataLoader

class SiamesePairDataset(TorchDataset):
    def __init__(self, pairs_labels):
        self.pairs_labels = pairs_labels
    
    def __len__(self):
        return len(self.pairs_labels)
    
    def __getitem__(self, idx):
        pair, label = self.pairs_labels[idx]
        g1, g2 = pair
        return g1, g2, label


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
    # triplets = []
    pairs = []
    labels = []

    for cls, graphs in class_dict.items():
        cls_name = reverse_cat_dict[cls]
        for i in range(len(graphs)):
            graph_a = graphs[i]
            for j in range(i + 1, len(graphs)):
                pairs.append((graph_a, graphs[j]))
                labels.append(1.0)
                # graph_p = graphs[j]

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
                # triplets.append((graph_a, graph_p, hard_graph_n))
                pairs.append((graph_a, hard_graph_n))
                labels.append(0.0)

                # if hn_cls is None:
                #     print(f'hn_cls is None for cls_name: {cls_name}')

                # make graph_n with easy negative
                another_cls = random.choice(list(set(class_dict.keys()) - {cls} - {hn_cls}))
                graph_n = random.choice(class_dict[another_cls])
                # triplets.append((graph_a, graph_p, graph_n))
                pairs.append((graph_a, graph_n))
                labels.append(0.0)
    # return triplets
    return list(zip(pairs, labels))


# data_dir = './better_processed_data'
# data_dir = './data630d3processed'
# model_file_name = 'best_630d3_model.pth'
# loss_img_name = 'loss_curve_d3.png'
data_dir = './data630d3processednormDict'
# model_file_name = 'best_630d3norm_hnm_model3_Alpha30_random.pth'
# loss_img_name = 'loss_curve_d3norm_hnm3_Alpha30_random.png'
model_file_name = 'best_630d3norm_authsense.pth'
loss_img_name = 'loss_curve_d3norm_authsense.png'


data_files = [f for f in os.listdir(data_dir) if f.endswith('.pt')]
dataset = [torch.load(os.path.join(data_dir, f), weights_only=False) for f in data_files]
transformed_dataset = generate_valid_triplets(dataset)

random.shuffle(transformed_dataset)

# exit(0)

train_ratio = 0.8
train_dataset = transformed_dataset[:int(train_ratio * len(transformed_dataset))]
test_dataset = transformed_dataset[int(train_ratio * len(transformed_dataset)):]

train_dataset_wrapper = SiamesePairDataset(train_dataset)
test_dataset_wrapper = SiamesePairDataset(test_dataset)

def siamese_collate(batch):
    g1_list, g2_list, labels = zip(*batch)
    
    g1_batch = Batch.from_data_list(list(g1_list))
    g2_batch = Batch.from_data_list(list(g2_list))
    labels_tensor = torch.tensor(labels, dtype=torch.float32)
    
    return g1_batch, g2_batch, labels_tensor

# train_loader = DataLoader(train_dataset, batch_size=10, shuffle=True, follow_batch=['x'])
# test_loader = DataLoader(test_dataset, batch_size=10, shuffle=False)
train_loader = TorchDataLoader(
    train_dataset_wrapper, 
    batch_size=10, 
    shuffle=True, 
    collate_fn=siamese_collate
)
test_loader = TorchDataLoader(
    test_dataset_wrapper, 
    batch_size=10, 
    shuffle=False,
    collate_fn=siamese_collate
)


# Build the model, only use CPU as MPS is not supported for PyG
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
device = torch.device("cpu")
print(f'Using device: {device}')
# encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=64).to(device)
# encoder_model = GNNEncoder(input_dim=6, hidden_dim=16, output_dim=8).to(device)
encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=32).to(device)
# encoder_model = GNNEncoderCP(input_dim=6, hidden_dim=64, output_dim=64).to(device)
# model = TripletNet(encoder_model).to(device)
pretrained_GNN_path = 'best_630d3norm_hnm_meanpool_a4_random.pth'
checkpoint = torch.load(pretrained_GNN_path, map_location=device, weights_only=False)

# 提取 encoder 的权重（假设之前用 TripletNet 训练）
# 需要根据保存的结构调整
if 'model_state_dict' in checkpoint:
    state_dict = checkpoint['model_state_dict']
    # 如果保存的是 TripletNet，需要提取 embedding_net 部分
    encoder_state_dict = {k.replace('embedding_net.', ''): v 
                          for k, v in state_dict.items() 
                          if k.startswith('embedding_net.')}
    encoder_model.load_state_dict(encoder_state_dict)
else:
    encoder_model.load_state_dict(checkpoint)

print("✅ Loaded pretrained encoder weights")

# 2. 冻结 encoder 参数
for param in encoder_model.parameters():
    param.requires_grad = False

print("✅ Frozen encoder parameters")

model = AuthSenseSiemase(encoder_model).to(device)

trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
total_params = sum(p.numel() for p in model.parameters())
print(f"Trainable parameters: {trainable_params:,} / {total_params:,}")


# # optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
# # optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
# optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
# # scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=3)
# # criterion = torch.nn.BCEWithLogitsLoss()
# # criterion = torch.nn.TripletMarginLoss(margin=4.0, p=2)  # Triplet loss with margin
# criterion = torch.nn.TripletMarginLoss(margin=4.0, p=2)  # Triplet loss with margin
# scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=7)
optimizer = torch.optim.AdamW(
    filter(lambda p: p.requires_grad, model.parameters()),
    lr=0.001, 
    weight_decay=1e-4
)
criterion = torch.nn.BCELoss()  # Binary Cross-Entropy for Siamese
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=7
)

def train():
    model.train()
    total_loss = 0
    correct = 0
    total = 0

    for g1, g2, labels in train_loader:  # Iterate in batches over the training dataset.
        optimizer.zero_grad()  # Clear gradients.
        # g1, g2, g3 = data
        g1 = g1.to(device)
        g2 = g2.to(device)
        # g3 = g3.to(device)
        labels = labels.to(device).unsqueeze(1)
        # out = model(g1, g2, g3).squeeze()  # Perform a single forward pass.
        # out = model(g1, g2, g3)
        decision = model(g1, g2)
        # print(out)
        # loss_outputs = criterion(*out)  # Compute the loss.
        loss = criterion(decision, labels)
        # loss = loss_outputs[0] if type(loss_outputs) in (tuple, list) else loss_outputs
        # total_loss += loss.item()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        total_loss += loss.item()

        # Accuracy
        predicted = (decision > 0.5).float()
        correct += (predicted == labels).sum().item()
        total += labels.size(0)
         
    # return total_loss / len(train_loader)
    avg_loss = total_loss / len(train_loader)
    accuracy = 100. * correct / total
    
    return avg_loss, accuracy

def test():
    model.eval()
    # val_loss = 0
    total_loss = 0
    correct = 0
    total = 0
    # with torch.no_grad():
    #     for data in test_loader:
    #         g1, g2, g3 = data
    #         g1, g2, g3 = g1.to(device), g2.to(device), g3.to(device)
    #         outputs = model(g1, g2, g3)
    #         if type(outputs) not in (tuple, list):
    #             outputs = (outputs,)
    #         loss_outputs = criterion(*outputs)
    #         loss = loss_outputs[0] if type(loss_outputs) in (tuple, list) else loss_outputs
    #         val_loss += loss.item()
    # return val_loss / len(test_loader)
    with torch.no_grad():
        for g1, g2, labels in test_loader:
            g1 = g1.to(device)
            g2 = g2.to(device)
            labels = labels.to(device).unsqueeze(1)
            
            decision = model(g1, g2)
            loss = criterion(decision, labels)
            
            total_loss += loss.item()
            
            predicted = (decision > 0.5).float()
            correct += (predicted == labels).sum().item()
            total += labels.size(0)
    
    avg_loss = total_loss / len(test_loader)
    accuracy = 100. * correct / total
    
    return avg_loss, accuracy

best_test_loss = float('inf')

# train_losses = []
# test_losses = []
train_losses = []
test_losses = []
train_accs = []
test_accs = []

# for epoch in range(1, 100):
#     train_loss = train()
#     test_loss = test()

#     train_losses.append(train_loss)
#     test_losses.append(test_loss)

#     if test_loss < best_test_loss:
#         # best_test_acc = test_loss
#         best_test_loss = test_loss
#         torch.save({
#             'epoch': epoch,
#             'model_state_dict': model.state_dict(),
#             'optimizer_state_dict': optimizer.state_dict(),
#             'loss': train_loss,
#             'accuracy': test_loss,
#         }, model_file_name)  # Save to current directory

#     scheduler.step(test_loss)

#     if epoch % 5 == 0:
#         print(f'Epoch: {epoch:03d}, Train loss: {train_loss:.4f}, Test loss: {test_loss:.4f}')
for epoch in range(1, 100):
    train_loss, train_acc = train()
    test_loss, test_acc = test()

    train_losses.append(train_loss)
    test_losses.append(test_loss)
    train_accs.append(train_acc)
    test_accs.append(test_acc)

    if test_loss < best_test_loss:
        best_test_loss = test_loss
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': test_loss,
            'accuracy': test_acc,
        }, model_file_name)

    scheduler.step(test_loss)

    if epoch % 5 == 0:
        print(f'Epoch: {epoch:03d}, Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, '
              f'Test Loss: {test_loss:.4f}, Test Acc: {test_acc:.2f}%')


# plt.figure(figsize=(10, 6))
# plt.plot(train_losses, label='Train Loss')
# plt.plot(test_losses, label='Test Loss')
# plt.xlabel('Epoch')
# plt.ylabel('Loss')
# plt.title('Train and Test Loss over Epochs')
# plt.legend()
# plt.grid(True)
# plt.savefig(loss_img_name)  # 可选：保存图像
# plt.show()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

ax1.plot(train_losses, label='Train Loss')
ax1.plot(test_losses, label='Test Loss')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.set_title('Loss over Epochs')
ax1.legend()
ax1.grid(True)

ax2.plot(train_accs, label='Train Accuracy')
ax2.plot(test_accs, label='Test Accuracy')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy (%)')
ax2.set_title('Accuracy over Epochs')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig(loss_img_name)
plt.show()

print(f"\n✅ Training completed!")
print(f"Best test loss: {best_test_loss:.4f}")
print(f"Model saved to: {model_file_name}")

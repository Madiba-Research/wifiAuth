from collections import defaultdict
import os
import random
import torch
# from torch_geometric.datasets import TUDataset
from torch_geometric.loader import DataLoader
from torch_geometric.data import Batch

from models.Encoderdemo import SiameseGNN


def generate_valid_pairs(dataset):
    class_dict = defaultdict(list)
    for data in dataset:
        class_dict[data.y].append(data)
    # first generate all equalized pairs
    pairs = []
    for cls, graphs in class_dict.items():
        for i in range(len(graphs)):
            for j in range(i+1, len(graphs)):
                pairs.append((graphs[i], graphs[j], 1))
    pair_num = len(pairs)
    # then we generate same amount of unequalized pairs
    for i in range(pair_num):
        c1, c2 = random.sample(list(class_dict.keys()), 2)
        g1 = random.choice(class_dict[c1])
        g2 = random.choice(class_dict[c2])
        pairs.append((g1, g2, 0))
    random.shuffle(pairs)
    num_1 = sum([1 for _, _, label in pairs if label == 1])
    num_0 = sum([1 for _, _, label in pairs if label == 0])
    print(f'Number of positive pairs: {num_1}')
    print(f'Number of negative pairs: {num_0}')
    return pairs


def generate_pairs(dataset, samples_per_class=30):
    class_dict = defaultdict(list)
    for data in dataset:
        class_dict[data.y.item()].append(data)
    
    pairs = []
    # 生成正样本
    for cls, graphs in class_dict.items():
        for _ in range(samples_per_class):
            g1, g2 = random.sample(graphs, 2)
            pairs.append( (g1, g2, 1) )
    # 生成负样本
    for _ in range(len(class_dict)*samples_per_class):
        c1, c2 = random.sample(list(class_dict.keys()), 2)
        g1 = random.choice(class_dict[c1])
        g2 = random.choice(class_dict[c2])
        pairs.append( (g1, g2, 0) )
    random.shuffle(pairs)
    return pairs

def transform_data(dataset):
    transformed_data = []
    for i in range(len(dataset)):
        for j in range(i + 1, len(dataset)):
            data1 = dataset[i]
            data2 = dataset[j]
            x = (data1, data2)
            y = 1 if data1.y == data2.y else 0
            transformed_data.append((x, y))
    return transformed_data


# Load the dataset
data_dir = './processed_data'
data_files = [f for f in os.listdir(data_dir) if f.endswith('.pt')]
dataset = [torch.load(os.path.join(data_dir, f), weights_only=False) for f in data_files]
transformed_dataset = generate_valid_pairs(dataset)


# Only use the first 50 for testing
# dataset = TUDataset(root='/tmp/ENZYMES', name='ENZYMES')
# transformed_dataset = transform_data(dataset)
# transformed_dataset = generate_pairs(dataset, samples_per_class=50)

train_ratio = 0.8
train_dataset = transformed_dataset[:int(train_ratio * len(transformed_dataset))]
test_dataset = transformed_dataset[int(train_ratio * len(transformed_dataset)):]

# Transform the dataset
# transformed_dataset = transform_data(dataset)
# train_dataset = transformed_dataset[:2000]
# test_dataset = transformed_dataset[2000:]

print(f'Number of training graphs: {len(train_dataset)}')
print(f'Number of test graphs: {len(test_dataset)}')

def collate_fn(batch):
    g1_list, g2_list, labels = [], [], []
    for (g1, g2), label in batch:
        g1_list.append(g1)
        g2_list.append(g2)
        labels.append(label)
    batch_g1 = Batch.from_data_list(g1_list)
    batch_g2 = Batch.from_data_list(g2_list)
    return (batch_g1, batch_g2), torch.tensor(labels)


train_loader = DataLoader(train_dataset, batch_size=5, shuffle=True, follow_batch=['x'])
test_loader = DataLoader(test_dataset, batch_size=5, shuffle=False)

# Build the model
# device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
device = torch.device("cpu")
print(f'Using device: {device}')
# model = SiameseGNN(input_dim=dataset.num_features, hidden_dim=64, output_dim=64).to(device)
model = SiameseGNN(input_dim=6, hidden_dim=64, output_dim=64).to(device)

# optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)
# scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=3)
criterion = torch.nn.BCEWithLogitsLoss()

def train():
    model.train()
    total_loss = 0
    for data in train_loader:  # Iterate in batches over the training dataset.
        optimizer.zero_grad()  # Clear gradients.
        g1, g2, labels = data
        g1 = g1.to(device)
        g2 = g2.to(device)
        labels = labels.float().squeeze().to(device)
        out = model(g1, g2).squeeze()  # Perform a single forward pass.
        # print(out)
        loss = criterion(out, labels)  # Compute the loss.
        total_loss += loss.item()
        loss.backward()  # Derive gradients.
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
         
    return total_loss / len(train_loader)

def test(loader):
    model.eval()

    correct = 0
    with torch.no_grad():
        for data in loader:
            g1, g2, labels = data
            g1, g2 = g1.to(device), g2.to(device)
            labels = labels.float().to(device)
            out = model(g1, g2).squeeze()
            # print(out)
            pred = torch.sigmoid(out) > 0.5
            correct += (pred == labels).sum().item()
    return correct / len(loader.dataset)

best_test_acc = 0.0
for epoch in range(1, 300):
    train_loss = train()
    train_acc = test(train_loader)
    # scheduler.step(train_acc)
    test_acc = test(test_loader)
    if test_acc > best_test_acc:
        best_test_acc = test_acc
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'loss': train_loss,
            'accuracy': test_acc,
        }, 'best_model.pth')  # Save to current directory
    if epoch % 20 == 0:
        print(f'Epoch: {epoch:03d}, Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}')


    
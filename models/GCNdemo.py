import torch
from torch_geometric.nn import GCNConv

import torch.nn.functional as F

class MyGCNConv(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GCNConv, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)

# Example usage:
# model = GCN(in_channels=dataset.num_node_features, hidden_channels=16, out_channels=dataset.num_classes)
# out = model(data.x, data.edge_index)
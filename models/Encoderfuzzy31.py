import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import GCNConv, global_mean_pool, global_max_pool
from torch_geometric.nn import TransformerConv


# we take this GNNEncoder as the EmbeddingNet
class GNNEncoder(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()

        # self.conv1 = GCNConv(input_dim, hidden_dim)
        # self.conv2 = GCNConv(hidden_dim, hidden_dim)
        # self.conv3 = GCNConv(hidden_dim, output_dim)

        self.conv1 = TransformerConv(input_dim, hidden_dim, edge_dim=1)
        self.conv2 = TransformerConv(hidden_dim, hidden_dim, edge_dim=1)
        self.conv3 = TransformerConv(hidden_dim, hidden_dim, edge_dim=1)
        self.conv4 = TransformerConv(hidden_dim, output_dim, edge_dim=1)
        # self.conv4 = TransformerConv(hidden_dim, output_dim // 2, edge_dim=1)

        

        self.bn1 = torch.nn.BatchNorm1d(hidden_dim)
        self.bn2 = torch.nn.BatchNorm1d(hidden_dim)
        self.bn3 = torch.nn.BatchNorm1d(hidden_dim)

        self.bn4 = torch.nn.BatchNorm1d(output_dim)
        # self.pool = global_add_pool

        # for log_auth_distance_sigma2_norm_hn
        # self.pool = global_mean_pool

        # # for log_auth_alpha15
        # self.pool = global_max_pool

        self.pool_fc = nn.Sequential(
            nn.Linear(output_dim * 2, output_dim),  # 2倍因为拼接了mean和max
            nn.LayerNorm(output_dim),  # 添加归一化
            nn.ReLU(),
            nn.Dropout(0.1),  # 防止过拟合
            nn.Linear(output_dim, output_dim)
        )

    def forward(self, x, edge_index, batch, edge_attr=None):
        if edge_attr is None:
            raise ValueError("edge_attr is required for this model")

        # x = self.conv1(x, edge_index, edge_attr).relu()
        # x = self.bn1(x)

        # x = self.conv2(x, edge_index, edge_attr).relu()
        # x = self.bn2(x)
        # x = self.conv3(x, edge_index, edge_attr).relu()

        # x = self.bn3(x)
        # x = self.conv4(x, edge_index, edge_attr)

        # with residual connection
        x = self.conv1(x, edge_index, edge_attr)
        x = self.bn1(x)
        x = F.relu(x)

        res = x
        x = self.conv2(x, edge_index, edge_attr)
        x = self.bn2(x)
        x = x + res  # Residual connection
        x = F.relu(x)
        # --- Block 2 ---
        res = x
        x = self.conv3(x, edge_index, edge_attr)
        x = self.bn3(x)
        x = x + res  # Residual connection
        x = F.relu(x)
        x = self.conv4(x, edge_index, edge_attr)
        x = self.bn4(x)
        x = F.relu(x)

        # x = x + self.conv2(x, edge_index)
        # x = x + self.conv3(x, edge_index)
        
        # graph_embedding = global_mean_pool(x, batch)
        # for both log_auth_distance_sigma2_norm_hn and log_auth_alpha15
        # graph_embedding = self.pool(x, batch)

        mean_pool = global_mean_pool(x, batch)
        max_pool = global_max_pool(x, batch)
        combined = torch.cat([mean_pool, max_pool], dim=1)
        graph_embedding = self.pool_fc(combined)

        # mean_pool = global_mean_pool(x, batch)
        # max_pool = global_max_pool(x, batch)
        # graph_embedding = torch.cat([mean_pool, max_pool], dim=1)

        return graph_embedding
    

    # def forward(self, x, edge_index, batch):

    #     x = self.conv1(x, edge_index).relu()
    #     x = self.bn1(x)

    #     x = self.conv2(x, edge_index).relu()
    #     x = self.bn2(x)
    #     x = self.conv3(x, edge_index)

    #     # x = x + self.conv2(x, edge_index)
    #     # x = x + self.conv3(x, edge_index)
        
    #     # graph_embedding = global_mean_pool(x, batch)
    #     graph_embedding = self.pool(x, batch)
    #     return graph_embedding

    
    
class GNNEncoderCP(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, pool=global_mean_pool, dropout=0.5, activation=F.relu):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, output_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
        self.bn3 = nn.BatchNorm1d(output_dim)
        self.pool = pool
        self.dropout = nn.Dropout(p=dropout)
        self.activation = activation

    def forward(self, x, edge_index, batch):
        x = self.activation(self.conv1(x, edge_index))
        x = self.bn1(x)
        x = self.dropout(x)

        x = self.activation(self.conv2(x, edge_index))
        x = self.bn2(x)
        x = self.dropout(x)

        x = self.conv3(x, edge_index)
        x = self.bn3(x)

        graph_embedding = self.pool(x, batch)
        return graph_embedding


# https://github.com/adambielski/siamese-triplet/blob/master/networks.py
# For our SiameseNet and TripletNet, we add edge_index and batch when we call the forward function
class SiameseNet(nn.Module):
    def __init__(self, embedding_net):
        super(SiameseNet, self).__init__()
        self.embedding_net = embedding_net

    # def forward(self, x1, x2):
    #     output1 = self.embedding_net(x1)
    #     output2 = self.embedding_net(x2)
    #     return output1, output2

    def forward(self, g1, g2):
        output1 = self.embedding_net(g1.x, g1.edge_index, g1.batch)
        output2 = self.embedding_net(g2.x, g2.edge_index, g2.batch)
        return output1, output2

    def get_embedding(self, x):
        return self.embedding_net(x)


# class TripletNet(nn.Module):
#     def __init__(self, embedding_net):
#         super(TripletNet, self).__init__()
#         self.embedding_net = embedding_net

#     # def forward(self, x1, x2, x3):
#     #     output1 = self.embedding_net(x1)
#     #     output2 = self.embedding_net(x2)
#     #     output3 = self.embedding_net(x3)
#     #     return output1, output2, output3

#     def forward(self, g1, g2, g3):
#         output1 = self.embedding_net(g1.x, g1.edge_index, g1.batch)
#         output2 = self.embedding_net(g2.x, g2.edge_index, g2.batch)
#         output3 = self.embedding_net(g3.x, g3.edge_index, g3.batch)
#         return output1, output2, output3

#     def get_embedding(self, x):
#         return self.embedding_net(x)

class TripletNet(nn.Module):
    def __init__(self, embedding_net):
        super(TripletNet, self).__init__()
        self.embedding_net = embedding_net

    # def forward(self, x1, x2, x3):
    #     output1 = self.embedding_net(x1)
    #     output2 = self.embedding_net(x2)
    #     output3 = self.embedding_net(x3)
    #     return output1, output2, output3

    def forward(self, g1, g2, g3):
        output1 = self.embedding_net(g1.x, g1.edge_index, g1.batch, g1.edge_attr)
        output2 = self.embedding_net(g2.x, g2.edge_index, g2.batch, g2.edge_attr)
        output3 = self.embedding_net(g3.x, g3.edge_index, g3.batch, g3.edge_attr)
        return output1, output2, output3

    def get_embedding(self, x):
        return self.embedding_net(x)



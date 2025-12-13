import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import GCNConv, GATConv, global_mean_pool, global_add_pool

# a test model for graph matching
# SiameseGNN model
class GNNEncoder(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, output_dim)
        self.bn1 = torch.nn.BatchNorm1d(hidden_dim)
        self.bn2 = torch.nn.BatchNorm1d(hidden_dim)
        # self.pool = global_add_pool
        self.pool = global_mean_pool

    def forward(self, x, edge_index, batch):

        x = self.conv1(x, edge_index).relu()
        x = self.bn1(x)

        x = self.conv2(x, edge_index).relu()
        x = self.bn2(x)
        x = self.conv3(x, edge_index)

        # x = x + self.conv2(x, edge_index)
        # x = x + self.conv3(x, edge_index)
        
        # graph_embedding = global_mean_pool(x, batch)
        graph_embedding = self.pool(x, batch)
        return graph_embedding
    
class GATEncoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, output_dim=64, heads=4):
        super().__init__()
        self.conv1 = GATConv(input_dim, hidden_dim, heads=heads)  # 多头注意力
        self.conv2 = GATConv(hidden_dim*heads, hidden_dim, heads=heads)
        self.conv3 = GATConv(hidden_dim*heads, output_dim, heads=1)  # 最后一层单头
        self.skip = nn.Linear(input_dim, output_dim)  # 残差连接
        
    def forward(self, x, edge_index, batch):
        # 初始跳跃连接
        identity = self.skip(x)
        
        # 第一层GAT
        x = self.conv1(x, edge_index)
        x = F.leaky_relu(x, negative_slope=0.2)
        
        # 第二层GAT
        x = self.conv2(x, edge_index)
        x = F.leaky_relu(x, negative_slope=0.2)
        
        # 第三层GAT + 残差
        x = self.conv3(x, edge_index) + identity
        
        # 图级池化
        return global_add_pool(x, batch)
    
    
class SimilarityPredictor(torch.nn.Module):
    def __init__(self, embedding_dim):
        super().__init__()
        # self.dense = torch.nn.Linear(embedding_dim * 2, 1)
        self.mlp = nn.Sequential(
            # nn.Linear(embedding_dim*2, 64),
            nn.Linear(embedding_dim * 4, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)
            # nn.Sigmoid()
        )
        
    def forward(self, emb1, emb2):
        # combined = torch.cat([emb1, emb2], dim=-1)
        # # similarity = torch.sigmoid(self.dense(combined))
        # similarity = self.dense(combined)
        # return similarity
        diff = torch.abs(emb1 - emb2)  # 捕捉差异特征
        prod = emb1 * emb2             # 捕捉相似性特征
        combined = torch.cat([emb1, emb2, diff, prod], dim=-1)
        # combined = torch.cat([diff], dim=-1)
        # print(f"拼接后维度: {combined.shape}")
        return self.mlp(combined)
    
class SiameseGNN(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=128, output_dim=64):
        super().__init__()
        self.encoder = GNNEncoder(input_dim, hidden_dim, output_dim)
        # self.encoder = GATEncoder(input_dim, hidden_dim, output_dim)
        self.predictor = SimilarityPredictor(output_dim)

    def forward(self, graph1, graph2):
        emb1 = self.encoder(graph1.x, graph1.edge_index, graph1.batch)
        emb2 = self.encoder(graph2.x, graph2.edge_index, graph2.batch)
        return self.predictor(emb1, emb2)
    
# criterion = torch.nn.BCEWithLogitsLoss()
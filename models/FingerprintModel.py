import torch
import torch.nn as nn
import torch.nn.functional as F


class MLPEncoder(nn.Module):
    """
    最简单的MLP编码器 - 用作基线
    """
    def __init__(self, 
                 input_dim=100,
                 embed_dim=32):
        super().__init__()
        
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(128, embed_dim)
        )
        
    def forward(self, x):
        """
        x: [batch, 100] - 直方图输入
        """
        x = self.mlp(x)  # [batch, embed_dim]
        
        # L2归一化（关键！）
        x = F.normalize(x, p=2, dim=1)
        
        return x


class CNNENcoder(nn.Module):
    def __init__(self, 
                 input_dim=100,
                 embed_dim=32):
        super().__init__()

        self.conv_layers = nn.Sequential(
            # 输入: [batch, 1, 100]
            nn.Conv1d(1, 32, kernel_size=5, padding=2),  # 捕获5个相邻bin的模式
            nn.ReLU(),
            nn.MaxPool1d(2),  # [batch, 32, 50]
            
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),  # [batch, 64, 25]
        )
        
        # 全连接层
        self.mlp = nn.Sequential(
            nn.Linear(64 * 25, 256),  # 25是池化后的长度
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            
            nn.Linear(128, embed_dim)
        )
    
    def forward(self, x):

        # 添加channel维度: [batch, 100] -> [batch, 1, 100]
        x = x.unsqueeze(1)
        
        # 卷积提取特征
        x = self.conv_layers(x)  # [batch, 64, 25]
        
        # 展平
        x = x.view(x.size(0), -1)  # [batch, 64*25]
        
        # MLP编码
        x = self.mlp(x)  # [batch, embed_dim]
        
        # # L2归一化
        # x = F.normalize(x, p=2, dim=1)
        
        return x

    

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
        output1 = self.embedding_net(g1)
        output2 = self.embedding_net(g2)
        output3 = self.embedding_net(g3)
        return output1, output2, output3

    def get_embedding(self, x):
        return self.embedding_net(x)
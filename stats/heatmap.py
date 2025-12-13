import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

users = [f'u{i}' for i in range(5)]

# 构建类型矩阵
matrix_type = np.array([
    ['TAR', 'FAR', 'TRR', 'TRR', 'TRR'],
    ['TRR', 'TAR', 'TRR', 'TRR', 'TRR'],
    ['TRR', 'TRR', 'TAR', 'TRR', 'TRR'],
    ['TRR', 'TRR', 'TRR', 'TAR', 'TRR'],
    ['TRR', 'TRR', 'TRR', 'TRR', 'TAR']
])

# 构建数值矩阵（比例）
matrix_value = np.array([
    [1,1,0,0,0],  # u0 vs u1 FAR=1
    [0,1,0,0,0],
    [0,0,1,0,0],
    [0,0,0,1,0],
    [0,0,0,0,1]
])

fig, ax = plt.subplots(figsize=(6,6))

for i in range(5):
    for j in range(5):
        val = matrix_value[i,j]
        typ = matrix_type[i,j]
        # 颜色分区
        if typ == 'TAR':
            color = (0.0, 0.6, 0.0, 0.6 + 0.4*val)  # 深绿渐变
        elif typ == 'TRR':
            color = (0.85, 0.85, 0.85, 0.6 + 0.4*val)  # 灰色渐变
        elif typ == 'FAR':
            color = (1.0, 0.2, 0.2, 0.6 + 0.4*val)  # 红色渐变
        rect = plt.Rectangle((j,i),1,1,facecolor=color, edgecolor='black', lw=1)
        ax.add_patch(rect)

# 对角线加粗边框
for i in range(5):
    ax.add_patch(plt.Rectangle((i,i),1,1,fill=False,edgecolor='black',lw=2))

ax.set_xlim(0,5)
ax.set_ylim(0,5)
ax.set_xticks(np.arange(5)+0.5)
ax.set_yticks(np.arange(5)+0.5)
ax.set_xticklabels(users, fontsize=12)
ax.set_yticklabels(users, fontsize=12)
ax.invert_yaxis()
ax.set_aspect('equal')

plt.title("Pairwise Authentication Matrix", fontsize=14, pad=12)
plt.xlabel("Claimed User", fontsize=12)
plt.ylabel("Actual User", fontsize=12)
plt.tight_layout()
plt.show()

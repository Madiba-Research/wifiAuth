import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# 创建2x4的子图布局
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()  # 将2D数组展平为1D，便于索引

# 为每个文件创建子图
for i in range(8):
    filename = f'sample_in_b{i}.txt'
    
    # 读取数据
    numbers = []
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                # 如果行里只包含 - . 0~9
                allowed_chars = set("-.0123456789")
                if all(c in allowed_chars for c in line) and line:
                    try:
                        numbers.append(float(line))
                    except ValueError:
                        pass  # 如果意外不能转成float，就忽略
        
        print(f"{filename}: {len(numbers)} numbers")
        
        if numbers:  # 如果有数据
            # 计算数据范围
            data_min = min(numbers)
            data_max = max(numbers)
            mean_val = np.mean(numbers)
            std_val = np.std(numbers)
            
            # 设置bin宽度为0.1
            bin_width = 0.1
            bins = np.arange(data_min, data_max + bin_width, bin_width)
            
            # 绘制直方图
            counts, bin_edges, patches = axes[i].hist(numbers, bins=bins, alpha=0.7, 
                                                    edgecolor='black', color='skyblue')
            
            # 拟合正态分布并绘制
            x_range = np.linspace(data_min, data_max, 100)
            normal_curve = stats.norm.pdf(x_range, mean_val, std_val)
            axes[i].plot(x_range, normal_curve, 'r-', linewidth=2, label='Normal Fit')

            # 标记均值线
            axes[i].axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'μ={mean_val:.3f}')
            
            # 标记一个标准差范围
            axes[i].axvline(mean_val + std_val, color='orange', linestyle=':', linewidth=2, 
                           label=f'±1σ ({std_val:.3f})')
            axes[i].axvline(mean_val - std_val, color='orange', linestyle=':', linewidth=2)
            
            # 标记两个标准差范围
            axes[i].axvline(mean_val + 2*std_val, color='green', linestyle='-.', linewidth=2, 
                           label=f'±2σ ({2*std_val:.3f})')
            axes[i].axvline(mean_val - 2*std_val, color='green', linestyle='-.', linewidth=2)
            

            # 显示统计信息
            mean_val = np.mean(numbers)
            axes[i].axvline(mean_val, color='red', linestyle='--', linewidth=2)
            
            # 设置标题和标签
            axes[i].set_title(f'b{i} (n={len(numbers)}, μ={mean_val:.3f}, σ={std_val:.3f})')
            axes[i].set_xlabel('Value')
            axes[i].set_ylabel('Density')
            axes[i].grid(True, alpha=0.3)
            axes[i].legend(fontsize='small')
        else:
            axes[i].text(0.5, 0.5, 'No Data', ha='center', va='center', 
                        transform=axes[i].transAxes, fontsize=12)
            axes[i].set_title(f'b{i}')
            
    except FileNotFoundError:
        print(f"File {filename} not found")
        axes[i].text(0.5, 0.5, 'File Not Found', ha='center', va='center', 
                    transform=axes[i].transAxes, fontsize=12)
        axes[i].set_title(f'b{i}')

# 调整子图间距
plt.tight_layout()

# 保存图片
plt.savefig("all_distributions_b0_to_b7.pdf", format="pdf", bbox_inches='tight')
plt.show()
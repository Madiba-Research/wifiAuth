import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


thresholds = np.linspace(1, 2, 100)
# far = ...
# frr = ...
# eer = 0.140
# eer_threshold = 0.276
with open("sf25user_tar_far_stat_2.txt", "r") as f:
    lines = f.readlines()[1:]  # 跳过标题行
    far = []
    frr = []
    for line in lines:
        parts = line.strip().split('\t')
        if len(parts) == 3:
            tar = float(parts[1])
            far_value = float(parts[2])
            far.append(far_value / 100.0)  # 转换为小数形式
            frr.append(1 - tar / 100.0)    # FRR = 1 - TAR
# eer = 0.07
eer_threshold = 1.185
eer_far = 0.0889
eer_frr = 0.0333


plt.figure(figsize=(8, 5))

# 画 FAR & FRR 曲线（让 matplotlib 使用默认配色）
line_far, = plt.plot(thresholds, far, label="Validation FAR", linewidth=2)
line_frr, = plt.plot(thresholds, frr, label="Validation FRR", linewidth=2)

# 画 EER 点（黑色星形）
star = plt.scatter([eer_threshold, eer_threshold], [eer_far, eer_frr], s=220, marker='*', color='black', zorder=5)

# 竖向虚线标出阈值
plt.axvline(eer_threshold, linestyle='--', color='black', linewidth=1.2)

# 网格与轴标签
plt.xlabel("Threshold", fontsize=12)
plt.ylabel("Error Rate", fontsize=12)
plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.7)

# ---------- 把 EER 文本放到图例里 ----------
eer_label = f"FAR={eer_far:.3f}\nFRR={eer_frr:.3f}\n@ t={eer_threshold:.3f}"

# 自定义 legend handles：使用已有 line 对象和一个星形 marker
legend_handles = [
    Line2D([0], [0], color=line_far.get_color(), lw=2),   # FAR 线条示例
    Line2D([0], [0], color=line_frr.get_color(), lw=2),   # FRR 线条示例
    Line2D([0], [0], marker='*', color='black', markersize=12, linestyle='None')  # EER 星形示例
]
legend_labels = ["Validation FAR", "Validation FRR", eer_label]

# 把图例放在右上角，白底黑框（和图中样式一致）
plt.legend(legend_handles, legend_labels, loc='upper right',
           fontsize=10, frameon=True, bbox_to_anchor=(0.98, 0.98), framealpha=1.0)

# 设定坐标范围，避免图例遮挡重要内容
plt.xlim(min(thresholds), max(thresholds))
plt.ylim(0, max(max(far), max(frr), eer_far, eer_frr) * 1.07)

plt.tight_layout()
plt.savefig("sf25user_frr_far.pdf", format="pdf", bbox_inches="tight")

plt.show()
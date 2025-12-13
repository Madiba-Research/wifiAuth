import matplotlib.pyplot as plt
import numpy as np

# def plot_roc_curve(fpr, tpr, labels):
#     plt.figure(figsize=(6, 6))
#     plt.scatter(fpr, tpr, color='blue', label='ROC points')

#     for x, y, label in zip(fpr, tpr, labels):
#         plt.text(x + 0.01, y - 0.01, label, fontsize=9, color='black')

#     plt.plot([0, 1], [0, 1], color='grey', lw=1, linestyle='--', label='Random guess')
#     plt.xlabel('False Positive Rate')
#     plt.ylabel('True Positive Rate')
#     plt.title('ROC Curve')
#     plt.legend(loc='lower right')
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig("roc_1.pdf", format="pdf")
#     plt.show()  

def plot_eer_curve(far, frr, labels):
    """
    绘制 FAR 和 FRR 曲线，并计算 ERR (Equal Error Rate)
    
    Args:
        far: False Accept Rate 列表
        frr: False Reject Rate 列表
        labels: 阈值标签列表
    """
    plt.figure(figsize=(8, 6))
    
    # 绘制 FAR 和 FRR 曲线
    x = np.arange(len(labels))
    plt.plot(x, far, 'b-o', label='FAR (False Accept Rate)', linewidth=2, markersize=8)
    plt.plot(x, frr, 'r-s', label='FRR (False Reject Rate)', linewidth=2, markersize=8)
    
    # 计算 ERR (Equal Error Rate) - 找到 FAR 和 FRR 最接近的点
    diff = np.abs(np.array(far) - np.array(frr))
    err_idx = np.argmin(diff)
    err_value = (far[err_idx] + frr[err_idx]) / 2
    err_threshold = labels[err_idx]
    
    # 标记 ERR 点
    plt.plot(err_idx, err_value, 'g*', markersize=15, label=f'EER = {err_value:.4f} @ threshold={err_threshold}')
    plt.axhline(y=err_value, color='green', linestyle='--', linewidth=1, alpha=0.5)
    
    # 在每个点上标注数值（只显示小数）
    for i, (f, r) in enumerate(zip(far, frr)):
        plt.text(i, f + 0.005, f'{f:.4f}', ha='center', fontsize=9, color='blue')
        plt.text(i, r - 0.008, f'{r:.4f}', ha='center', fontsize=9, color='red')
    
    plt.xlabel('Threshold', fontsize=12)
    plt.ylabel('Error Rate', fontsize=12)
    plt.title('EER Curve: FAR vs FRR', fontsize=14, fontweight='bold')
    plt.xticks(x, labels)

    # 动态设置 y 轴范围，更紧凑
    min_val = min(min(far), min(frr))
    max_val = max(max(far), max(frr))
    margin = (max_val - min_val) * 0.15  # 15% 边距
    plt.ylim(min_val - margin, max_val + margin)

    # plt.ylim(-0.05, max(max(far), max(frr)) + 0.1)
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图片
    # plt.savefig("err_curve.pdf", format="pdf")
    plt.savefig("err_curve_u25.pdf", format="pdf")
    print(f"EER: {err_value:.4f}")
    print(f"EER Threshold: {err_threshold}")
    print(f"At EER point - FAR: {far[err_idx]:.4f}, FRR: {frr[err_idx]:.4f}")
    
    plt.show()


def calculate_eer(far, frr, labels):
    """
    单独计算 EER
    
    Returns:
        err_value: ERR 数值
        err_threshold: ERR 对应的阈值
    """
    diff = np.abs(np.array(far) - np.array(frr))
    err_idx = np.argmin(diff)
    err_value = (far[err_idx] + frr[err_idx]) / 2
    err_threshold = labels[err_idx]
    
    return err_value, err_threshold, err_idx



if __name__ == "__main__":
    # far = [0.0, 0.0, 0.02, 0.12, 0.22]
    # frr = [0.22, 0.06, 0.02, 0.0, 0.0]
    # labels = ["1.0", "1.5", "2.0", "2.5", "3.0"]

    far = [0.1211, 0.0842, 0.0789, 0.0474, 0.0368, 0.0263]
    frr = [0.0579, 0.0684, 0.0789, 0.0789, 0.0789, 0.0947]
    labels = ["0.9", "1.0", "1.1", "1.2", "1.3", "1.4"]

    plot_eer_curve(far, frr, labels)
    
    # 单独计算 EER
    err, threshold, idx = calculate_eer(far, frr, labels)
    print(f"\n=== ERR Analysis ===")
    print(f"ERR: {err:.4f} ({err:.2%})")
    print(f"Best Threshold: {threshold}")
    print(f"FAR at ERR: {far[idx]:.4f}")
    print(f"FRR at ERR: {frr[idx]:.4f}")
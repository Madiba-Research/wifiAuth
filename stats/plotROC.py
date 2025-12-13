import matplotlib.pyplot as plt

def plot_roc_curve(fpr, tpr, labels):
    plt.figure(figsize=(6, 6))
    plt.scatter(fpr, tpr, color='blue', label='ROC points')

    for x, y, label in zip(fpr, tpr, labels):
        plt.text(x + 0.01, y - 0.01, label, fontsize=9, color='black')

    plt.plot([0, 1], [0, 1], color='grey', lw=1, linestyle='--', label='Random guess')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve')
    plt.legend(loc='lower right')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("roc_1.pdf", format="pdf")
    plt.show()  



if __name__ == "__main__":
    tpr = [1.0, 1.0, 0.96, 0.98, 0.98]
    fpr = [0.94, 0.94, 0.82, 0.28, 0.02]
    labels = ["1m & 2m", "", "3m", "5m", "7m"]

    plot_roc_curve(fpr, tpr, labels)
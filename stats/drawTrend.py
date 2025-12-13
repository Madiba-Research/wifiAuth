import re
import matplotlib.pyplot as plt

# 读取文件
numbers = []
with open('b_mean_0.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip()
        # 如果行里只包含 - . 0~9
        allowed_chars = set("-.0123456789")
        if all(c in allowed_chars for c in line) and line:
            # print("提取到的数字:", line)
            try:
                numbers.append(float(line))
            except ValueError:
                pass  # 如果意外不能转成float，就忽略

# # 用正则表达式提取所有浮点数（包含负数）
# numbers = re.findall(r'-?\d+\.\d+', text)
# numbers = [float(num) for num in numbers]

print("提取到的数字:", numbers)

# 画折线图
plt.figure(figsize=(10, 5))
plt.plot(numbers, marker='o')
# plt.title('Trend of Extracted Numbers')
plt.xlabel('Sample Index')
plt.ylabel('Value')
plt.grid(True)
plt.savefig("b_0.pdf", format="pdf")
plt.show()
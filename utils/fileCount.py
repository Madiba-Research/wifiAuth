import os
from collections import Counter

folder = '/Users/noname/mlprojects/gnn_demo/data630d3'
suffix_counts = Counter()

for filename in os.listdir(folder):
    if filename.endswith('.json'):
        name_without_ext = filename[:-5]  # 去掉 .json
        if '+' in name_without_ext:
            _, plus_part = name_without_ext.split('+', 1)
            # + 号后面，前 8 个是时间，剩下是后缀
            if len(plus_part) > 8:
                time_part = plus_part[:8]      # '18:17:54'
                suffix = plus_part[8:]         # 'ev08635p3'
                suffix_counts[suffix] += 1

# for suffix, count in suffix_counts.items():
#     print(f'{suffix}: {count}')
# 把结果转成 (后缀, 计数) 的元组列表，并按后缀排序
sorted_counts = sorted(suffix_counts.items(), key=lambda x: x[0])

# 打印
print(f'{"Suffix":20} Count')
print('-' * 30)
for suffix, count in sorted_counts:
    print(f'{suffix:20} {count}')
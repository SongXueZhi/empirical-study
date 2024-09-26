import pandas as pd


# 加载 .pkl 文件
df = pd.read_pickle('./all_changes_data/metrics.pkl')

# 将 DataFrame 转换为 .csv 文件
df.to_csv('metrics.csv', index=False)


# df = pd.read_csv('all_regression_bugs.csv')
# df.to_pickle('all_regression_bugs.pkl')


# def read_hashes_from_file(filename):
#     # 使用with语句安全地打开文件并读取每一行的hash值
#     with open(filename, 'r', encoding='utf-8') as file:
#         # 读取所有行，并移除每行末尾的换行符
#         hashes = {line.strip() for line in file}
#     return hashes


# # 文件名
# set1_filename = 'set1.txt'
# set2_filename = 'set2.txt'
#
# # 读取两个文件中的commit hash
# set1_hashes = read_hashes_from_file(set1_filename)
# set2_hashes = read_hashes_from_file(set2_filename)
#
# # 计算集合大小
# size_set1 = len(set1_hashes)
# size_set2 = len(set2_hashes)
#
# # 计算差集
# diff_set1_set2 = set1_hashes - set2_hashes
#
# print(f"Set1 的元素数量: {size_set1}")
# print(f"Set2 的元素数量: {size_set2}")
# print(f"Set1 和 Set2 的差集: {len(diff_set1_set2)}")
# for item in diff_set1_set2:
#     print(item)
#
# diff_set2_set1 = set2_hashes - set1_hashes
# print(f"Set2 和 Set1 的差集: {len(diff_set2_set1)}")
# for item in diff_set2_set1:
#     print(item)
#
# intersection = set1_hashes & set2_hashes
# print(f"Set1 和 Set2 的交集: {len(intersection)}")

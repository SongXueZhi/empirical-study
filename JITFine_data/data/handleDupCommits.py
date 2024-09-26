from collections import defaultdict


def process_strings(input_file_path, output_file_path):
    # 使用字典记录每个字符串出现的次数
    string_count = defaultdict(int)

    with open(input_file_path, 'r', encoding='utf-8') as infile, \
            open(output_file_path, 'w', encoding='utf-8') as outfile:
        for line in infile:
            # 去除行尾的换行符
            string = line.rstrip('\n')

            # 如果字符串已经在字典中存在，则在其后添加前缀
            if string_count[string] > 0:
                new_string = f"{string_count[string]}_{string}"
            else:
                new_string = string

            # 将处理后的字符串写入输出文件
            outfile.write(new_string + '\n')

            # 更新字典中的计数
            string_count[string] += 1


# 示例用法
input_file_path = 'input.txt'
output_file_path = 'output.txt'

process_strings(input_file_path, output_file_path)

#!/bin/bash

# 检查是否提供了输入文件作为参数
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

# 获取输入文件路径
input_file="$1"

# 检查文件是否存在
if [ ! -f "$input_file" ]; then
    echo "Error: File '$input_file' does not exist."
    exit 1
fi

# 逐行读取文件内容并执行 git clone 命令
while IFS= read -r line; do
    echo "Cloning repository: $line"
    git clone "$line"
done < "$input_file"

echo "All repositories have been cloned."
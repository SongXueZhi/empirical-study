# 给定项目列表和bic列表依此处理数据
# 1. 读取项目列表和bic列表
# 2. 生成项目的diff内容
# 3. 清理diff内容
import os
import subprocess
import re
from pathlib import Path
import pygit2

current_path = Path(__file__).resolve().parent.parent
project_dir = os.path.join(current_path, 'repos')


def get_commit_info(repo_path, bic_hash):
    """
    使用 git log 获取提交信息（用户信息和提交消息）。
    """
    # 使用 git log 获取提交信息
    command = ["git", "log", "--format=%H%n%an%n%ae%n%ad%n%cn%n%ce%n%cd%n%B", "-n", "1", bic_hash]
    result = subprocess.run(command, cwd=repo_path, capture_output=True, text=True)
    
    if result.returncode == 0:
        commit_info = result.stdout.strip()
        return commit_info
    else:
        print(f"Error getting commit info for {bic_hash} in {repo_path}: {result.stderr}")
        return ""
    
def generate_diff(repo_path, bic_hash):
    """
    生成指定提交（BIC）的diff内容。
    """
    # 生成提交的diff内容
    command = ["git", "diff", f"{bic_hash}^", bic_hash]
    result = subprocess.run(command, cwd=repo_path, capture_output=True, text=True)
    
    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Error generating diff for {bic_hash} in {repo_path}: {result.stderr}")
        return ""

def clean_diff_content(diff_content):
    # 移除与测试相关的更改
    diff_content = remove_test_changes(diff_content)
    # 移除行首和行尾的空格和制表符
    diff_content = re.sub(r'^[ \t]+|[ \t]+$', '', diff_content, flags=re.MULTILINE)
    # 将多个空格和制表符替换为单个空格
    diff_content = re.sub(r'[ \t]+', ' ', diff_content)
    # 移除多余的空行
    diff_content = re.sub(r'\n\s*\n', '\n', diff_content)
    return diff_content
        
def remove_test_changes(diff_content):
    """Remove changes related to test files from the diff content."""
    # Split the diff content into individual file diffs
    file_diffs = re.split(r'(diff --git a/.* b/.*\n)', diff_content)
    cleaned_diffs = []
    for i in range(1, len(file_diffs), 2):
        diff_header = file_diffs[i]
        diff_body = file_diffs[i+1] if i+1 < len(file_diffs) else ''
        match = re.search(r'diff --git a/(.*) b/.*\n', diff_header)
        if match:
            file_path = match.group(1)
            # Skip test files
            if 'test' not in file_path.lower() and 'tests' not in file_path.lower():
                cleaned_diffs.append(diff_header + diff_body)
    cleaned_diff_content = ''.join(cleaned_diffs)
    return cleaned_diff_content

def process_bugs(project_name, bic):
    repo_path = os.path.join(project_dir, project_name)
    diff_content = generate_diff(repo_path, bic)
    cleaned_diff_content = clean_diff_content(diff_content)
    commit_info = get_commit_info(repo_path, bic)
    return commit_info, cleaned_diff_content



# if __name__ == '__main__':
   
    #main()   
import os
import re
from pathlib import Path
import pandas as pd

current_path = Path(__file__).resolve().parent.parent

def clean_result(result):
    """
    清理模型的响应结果，将其拆分为标签和消息。
    """
    #删除消息的第一个引号和最后一个引号
    
    if result.startswith('"') and result.endswith('"'):
        result =  result[1:-1]
    
    # 检查响应是否以 'Yes' 或 'No' 开头
    if result.startswith('Yes') or result.startswith('No'):
        # 以第一个句号 '.' 分割
        parts = result.split('\n', 1)
        if len(parts) == 2:
            label = parts[0].strip()
            message = parts[1].strip()
        else:
            # 如果没有句号，整个内容作为消息
            label = parts[0].strip()
            message = ''
    else:
        # 如果不以 'Yes' 或 'No' 开头，将整个内容作为消息
        label = None
        message = result.strip()
    return label, message

def is_yes_or_no(label):
    return bool(re.fullmatch(r'yes|no', label, re.IGNORECASE))

def split_label_and_message(response_content):
    csv_path = os.path.join(current_path, 'data', 'analysis_results_30.csv')
    results_path = os.path.join(current_path, 'data', 'analysis_results_30_cleaned.csv')    
    
    results = pd.read_csv(csv_path)
    for index, row in results.iterrows():
        if pd.isna(row['label']) and pd.isna(row['message']):
            continue
        if pd.isna(row['label']) and pd.notna(row['message']):
            label_pre = row['message']
        else:
            label_pre = row['label']    
        label_pre = label_pre.replace('[', '').replace(']', '')
        if is_yes_or_no(label_pre):
            continue;
        label, message = clean_result(label_pre)
        results.at[index, 'label'] = label
        results.at[index, 'message'] = message
    print(results) 
    results.to_csv(results_path, index=False) 

def is_second_char_underscore(commit_hash):
    return len(commit_hash) > 1 and commit_hash[1] == '_'

def clean_double_bug_commit():
    csv_path = os.path.join(current_path, 'data', 'analysis_results_30_cleaned.csv')
    results = pd.read_csv(csv_path)
    for index, row in results.iterrows():
        commit_hash = row['commit_hash']
        if  not is_second_char_underscore(commit_hash):
            continue
        commit_hash = commit_hash[2:]
        match_rows = results[results['commit_hash'] == commit_hash]
        if not match_rows.empty:
            match_row = match_rows.iloc[0]  # 获取匹配的第一行
            results.at[index, 'label'] = match_row['label']
            results.at[index, 'message'] = match_row['message']
    print(results)
    results_path = os.path.join(current_path, 'data', 'analysis_results_cleaned0.csv')
    results.to_csv(results_path, index=False)

if __name__ == '__main__':
    csv_path = os.path.join(current_path, 'data', 'analysis_results_cleaned0.csv')
    results = pd.read_csv(csv_path)
     # 绘制 total_token_count 列的箱形图
    import matplotlib.pyplot as plt
     # 绘制 total_token_count 列的箱形图
    plt.figure(figsize=(10, 6))
    boxplot = results.boxplot(column=['total_token_count'])

    # 获取重要的统计值
    stats = results['total_token_count'].describe()
    min_val = stats['min']
    q1_val = stats['25%']
    median_val = stats['50%']
    q3_val = stats['75%']
    max_val = stats['max']

    # 标注重要的统计值，调整位置以避免遮挡
    plt.text(1.1, min_val, f'Min: {min_val}', ha='left', va='center', fontsize=8, color='blue')
    plt.text(1.1, q1_val, f'Q1: {q1_val}', ha='left', va='center', fontsize=8, color='blue')
    plt.text(1.1, median_val, f'Median: {median_val}', ha='left', va='center', fontsize=8, color='blue')
    plt.text(1.1, q3_val, f'Q3: {q3_val}', ha='left', va='center', fontsize=8, color='blue')
    plt.text(1.1, max_val, f'Max: {max_val}', ha='left', va='center', fontsize=8, color='blue')

    plt.title('Total Token Count Boxplot')
    plt.ylabel('Total Token Count')
    plt.show()

    print(stats)
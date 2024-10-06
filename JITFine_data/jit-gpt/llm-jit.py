import os
import re
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from tiktoken import encoding_for_model
from data_analysis import process_bugs
import pickle
from pathlib import Path
from tqdm import tqdm
import pandas as pd

current_path = Path(__file__).resolve().parent.parent

def count_tokens(text, model_name='gpt-4o-2024-08-06'):
    """Count the number of tokens in the text."""
    encoding = encoding_for_model(model_name)
    tokens = encoding.encode(text)
    return len(tokens)

def create_prompts(diff_content, commit_info):
    """创建用于代码审查的提示信息，包括提交信息。"""
    system_prompt = SystemMessage(content="""
You are an experienced software engineer specializing in code reviews and bug detection. Your goal is to analyze all code changes to determine whether they will introduce any bugs.
""".strip())

    user_prompt = HumanMessage(content=f"""
Here are the commit information and code changes from a git diff:

**Commit Information:**
{commit_info}

**Code Changes:**
{diff_content}

Please analyze these changes and determine if they will introduce any bugs.

- If you think the changes will introduce a bug, answer "Yes".
- If you think the changes will **not** introduce a bug, answer "No".

Then, explain your conclusion in one sentence.

**Response Format:**
[Yes/No]
[One-sentence explanation]
""".strip())

    return [system_prompt, user_prompt]



def split_label_and_message(response_content):
    """
    将模型的响应拆分为标签和消息。
    假设响应格式为：
    'Yes. [解释]'
    或
    'No. [解释]'
    """
    # 检查响应是否以 'Yes' 或 'No' 开头
    if response_content.startswith('Yes') or response_content.startswith('No'):
        # 以第一个句号 '.' 分割
        parts = response_content.split('.', 1)
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
        message = response_content.strip()
    return label, message
    
def main():
    ## columns=['project_name', 'commit_hash', 'ID']
    data = pickle.load(open(os.path.join(current_path, 'data', 'all_regression_bugs.pkl'), 'rb'))

    if not isinstance(data, pd.DataFrame):
        data = pd.DataFrame(data)

    # 添加新的列用于保存结果
    data['total_token_count'] = None
    data['label'] = None
    data['message'] = None

    for index, row in tqdm(data.iterrows(), total=data.shape[0]):
        project_name = row['project_name']
        bic = row['commit_hash']
        ID = row['ID']
        if index < 29:
            continue
        try:
            # 获取提交信息和清理后的代码差异
            commit_info, diff_content = process_bugs(project_name, bic)

            # 创建包含提交信息的提示
            messages = create_prompts(diff_content, commit_info)

            # 初始化 ChatOpenAI
            llm = ChatOpenAI(model_name='gpt-4', temperature=0)

            # 计算 token 数量
            total_token_count = count_tokens(messages[0].content + messages[1].content, model_name=llm.model_name)
            print(f"The total token count (prompt + diff content) is {total_token_count} tokens.")

            # 保存 token 数量到 DataFrame
            data.at[index, 'total_token_count'] = total_token_count

            # 检查 token 数量是否超过模型的上下文长度限制
            max_tokens = 8192  # 对于 GPT-4，视模型版本而定
            if total_token_count > max_tokens:
                print(f"Total token count exceeds the maximum context length for GPT-4. Skipping index {index}.")
                continue

            # 运行分析
            response = llm(messages)
            label, message = split_label_and_message(response.content)

            # 保存结果到 DataFrame
            data.at[index, 'label'] = label
            data.at[index, 'message'] = message
            print(response.content)

        except RateLimitError as e:
            print(f"RateLimitError encountered at index {index}: {e}")
            print("Skipping this item and continuing to the next one.")
            continue

        except Exception as e:
            print(f"An error occurred at index {index}: {e}")
            print("Skipping this item and continuing to the next one.")
            continue

    # 将更新后的 DataFrame 保存为 CSV 文件
    output_csv_path = os.path.join(current_path, 'data', 'analysis_results.csv')
    data.to_csv(output_csv_path, index=False)
    print(f"Results saved to {output_csv_path}")

if __name__ == '__main__':
    main()

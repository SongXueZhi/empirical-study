import pandas as pd
from pandas import DataFrame
from sql_manager import MySQLDatabase

def load_data(file_path:str)->DataFrame:
    data = pd.read_csv(file_path)
    return data

def select_groups_number(id:int):
    db = MySQLDatabase("10.176.34.95", "root", "1235", "regression")
    db.connect()
    result = db.fetch_query("select project, bic  from ")
    db.disconnect()
    return result

def parse_group_name(input_string):
    # 初始化一个空字典
    result = {}

    # 如果输入字符串为空，直接返回空字典
    if not input_string.strip():
        return result
    
    # 清理字符串，去除多余的空格
    cleaned_input = input_string.strip()
    
    # 按空格分割输入字符串，得到每个键值对的字符串
    pairs = cleaned_input.split()
    
    # 遍历每个键值对的字符串
    for pair in pairs:
        if ':' in pair:  # 确保字符串中包含冒号
            # 按冒号分割，得到键和值
            key, value = pair.split(':')
            if key and value:  # 确保键和值都不为空
                # 将键和值存入字典，值转换为整数类型
                result[key] = int(value)
    
    return result
    

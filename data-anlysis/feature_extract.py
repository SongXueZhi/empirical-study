import os
import pandas as pd
projects=[]
directory = '/Users/sxz/reg4j/'

# 定义列名
columns = ["NS", "ND", "NF", "Entropy", "LA", "LD", "LT", "FIX", "NDEV", "AGE", "NUC", "EXP", "REXP", "SEXP"]

# 创建一个空的 DataFrame，使用这些列名作为表头
df = pd.DataFrame(columns=columns)

def get_project_path(project_name):
    return os.path.join(directory,'meta_projects',project_name)

def extract_features(project_name,commit_id):
    project_path = get_project_path(project_name)
    print(project_path)
    

    # do something with project_path
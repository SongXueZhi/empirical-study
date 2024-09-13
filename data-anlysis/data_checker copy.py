from pandas import DataFrame
import re
from collections import defaultdict
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
import networkx as nx
import matplotlib.pyplot as plt


pattern_actions = re.compile(r'^\w+\(\d+\)(;\s*\w+\(\d+\))*$')
pattern_action = re.compile(r'(\w+)\((\d+)\)')
feat_keywords =['enhance','feat','enhancement']
refactor_keywords = ['refactor','Reimpl.']

class DataChecker:
    def check_data(self,data:DataFrame)->list:
        action_count= defaultdict(int)
        bug_action_list = [defaultdict(int) for _ in range(120)]
        for index, row in data.iterrows():
            if index > 119:
                break
            actionValid = False
            bic_actions = row['bic action type'].split(',')
            for i, bic_action in enumerate(bic_actions):
                if bic_action in feat_keywords:
                    bic_actions[i] = 'feat'
                elif bic_action in refactor_keywords:
                    bic_actions[i] = 'refactor'

            actions = row['actions']
            actions = actions.replace(' ', '').replace('；', ';').replace('，', ',').replace('、', ',').replace('\n', '').replace('（', '(').replace('）', ')').replace(':', '')
            if not pattern_actions.match(actions):
                print(f"Invalid actions: {index}")
                continue
            actions = pattern_action.findall(actions)
            transaction = []
            for action in actions:
                action_name = action[0]
                if action[0] in feat_keywords:
                   action_name = 'feat'
                elif action[0] in refactor_keywords:
                    action_name = 'refactor'
                if action_name in bic_actions:
                    actionValid = True
                bug_action_list[index][action_name] += int(action[1])    
                action_count[action_name] += int(action[1])
            if not actionValid:
                print(f"Invalid bic action: {index}")   
        return action_count, bug_action_list

if __name__ == '__main__':
    file_path = '/Users/sxz/Documents/coding/project/empirical-study/data-anlysis/resources/bugs.xlsx'
    sheet_name = '0709合并'  # 你可以更改为你想要读取的工作表名称
    excel_data = pd.read_excel(file_path, sheet_name=sheet_name)
      
    checker = DataChecker()
    action_count, bug_action_list = checker.check_data(excel_data)
    
    # 输出action统计结果
    print("Action Count:")
    for action, count in action_count.items():
        print(f"{action}: {count}")
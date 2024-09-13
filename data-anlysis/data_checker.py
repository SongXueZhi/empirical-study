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
        bug_action_list = [defaultdict(int) for _ in range(429)]
        for index, row in data.iterrows():
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


    # # 绘制图表
    # fig, ax = plt.subplots(2, 1, figsize=(12, 10))

    # # 每种action的数量分布
    # ax[0].bar(action_count.keys(), action_count.values(), color='skyblue')
    # ax[0].set_xlabel('Action Types')
    # ax[0].set_ylabel('Count')
    # ax[0].set_title('Action Count Distribution')
    # ax[0].tick_params(axis='x', rotation=45)

    # # 每行中平均拥有的actions中位数
    # ax[1].boxplot(actions_per_row, vert=False, patch_artist=True, 
    #               boxprops=dict(facecolor='skyblue', color='blue'),
    #               medianprops=dict(color='red'))
    # ax[1].set_xlabel('Number of Actions per Row')
    # ax[1].set_title('Distribution of Actions per Row')
    # ax[1].annotate(f'Median: {median_actions_per_row}', xy=(median_actions_per_row, 1), 
    #                xytext=(median_actions_per_row + 0.5, 1.1),
    #                arrowprops=dict(facecolor='red', shrink=0.05))

    # plt.tight_layout()
    # plt.show()
    # # 使用TransactionEncoder将事务列表转换为适合关联规则挖掘的格式
    # te = TransactionEncoder()
    # te_ary = te.fit(transactions).transform(transactions)
    # df = pd.DataFrame(te_ary, columns=te.columns_)

    # # 使用Apriori算法找到频繁项集
    # frequent_itemsets = apriori(df, min_support=0.1, use_colnames=True)

    # # 找到关联规则
    # rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)


    # # 输出频繁项集和关联规则
    # print("\nFrequent Itemsets:")
    # print(frequent_itemsets)

    # print("\nAssociation Rules:")
    # print(rules)

    # # 创建一个有向图
    # G = nx.DiGraph()

    # # 添加节点和边，并为边设置权重
    # for _, row in rules.iterrows():
    #     for antecedent in row['antecedents']:
    #         for consequent in row['consequents']:
    #             G.add_edge(antecedent, consequent, weight=row['lift'])

    # # 获取边权重用于绘图
    # weights = [G[u][v]['weight'] for u, v in G.edges()]

    # # 绘制网络图
    # pos = nx.spring_layout(G, k=2)
    # plt.figure(figsize=(12, 8))
    # nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='skyblue')
    # nx.draw_networkx_edges(G, pos, width=weights, alpha=0.7)
    # nx.draw_networkx_labels(G, pos, font_size=15, font_color='black')

    # # 添加边标签（权重）
    # edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
    # nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=12)

    # # 显示图形
    # plt.title('Association Rules Network')
    # plt.show()
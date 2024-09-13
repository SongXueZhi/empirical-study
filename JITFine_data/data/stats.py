import json
from collections import defaultdict

import pandas as pd
from prettytable import PrettyTable as pt

data = pd.read_pickle('./dataset/all_data.pkl')
print(data)
projects = data['project_name'].unique()
projects.sort()

table = pt()
df_data = []
commit_data = data[['project_name', 'commit_hash', 'is_buggy_commit']].copy()
commit_data = commit_data.drop_duplicates().reset_index(drop=True)
table.field_names = ['project', 'buggy commits', 'clean commits', 'ratio(buggy commits/all commits)']
table_summary = ['ALL', 0, 0, 0]
all_buggy_cnt = 0
all_clean_cnt = 0
project2commit = defaultdict(list)
for project in projects:
    # commit-level
    cur_data = commit_data[commit_data['project_name'] == project]
    project2commit[project] = commit_data['commit_hash'].unique()
    # print(project, cur_data.shape)
    clean_commits = cur_data[cur_data['is_buggy_commit'] == 0]
    buggy_commits = cur_data[cur_data['is_buggy_commit'] == 1]
    clean_cnt, buggy_cnt = len(clean_commits), len(buggy_commits)
    # print(clean_cnt, buggy_cnt)
    # ratio = f'{round(buggy_cnt * 100 / len(cur_data), 2)}% ({buggy_cnt} / {len(cur_data)})'
    ratio = '{:<5.2f}% ({:6d} / {:<6d})'.format(round(buggy_cnt * 100 / len(cur_data), 2), buggy_cnt, len(cur_data))
    table.add_row([project, buggy_cnt, clean_cnt, ratio])
    df_data.append([project, buggy_cnt, clean_cnt, ratio])
    all_buggy_cnt += buggy_cnt
    all_clean_cnt += clean_cnt
    table_summary[1] += buggy_cnt
    table_summary[2] += clean_cnt
# table_summary[
    # -1] = f'{round(all_buggy_cnt * 100 / (all_buggy_cnt + all_clean_cnt), 2)}% ({all_buggy_cnt} / {(all_buggy_cnt + all_clean_cnt)})'
table_summary[-1] = '{:<5.2f}% ({:6d} / {:<6d})'.format(round(all_buggy_cnt * 100 / (all_buggy_cnt + all_clean_cnt), 2), all_buggy_cnt, (all_buggy_cnt + all_clean_cnt))
table.add_row(table_summary)
df_data.append(table_summary)
print(table)
df = pd.DataFrame(df_data, columns=table.field_names)
print(df)
# df.to_excel('./dataset_statistics_commit_level_20220904.xlsx')
clean_commits = json.load(open('./dataset/clean_commits.json', 'rb'))
# print(clean_commits.keys())

buggy_changes_with_buggy_line = json.load(open('./dataset/buggy_changes_with_buggy_line.json', 'rb'))[-1]
# print(buggy_changes_with_buggy_line['ant-ivy'].keys())
table = pt()
df_data = []
table.field_names = ['project', 'buggy lines', 'clean lines', 'ratio(buggy lines/all lines)']

table_summary = ['ALL', 0, 0, 0]
all_buggy_cnt = 0
all_clean_cnt = 0
line_data = data[['project_name', 'changed_type', 'is_buggy_line', 'changed_line']].copy()
# line_data = line_data.drop_duplicates().reset_index(drop=True)
lines = dict()
buggy = 0
clean = 0
cnt = 0
for project in projects:
    commits = buggy_changes_with_buggy_line[project]
    lines[project] = [0, 0]
    print(len(clean_commits[project]))

    for c in commits.keys():
        if c not in project2commit[project]:
            cnt += 1
            continue
        files = commits[c]['added_buggy_level']
        for f in files.keys():
            lines[project][0] += len(files[f]['added_buggy'])
            lines[project][1] += len(files[f]['added_clean'])
            buggy += len(files[f]['added_buggy'])
            clean += len(files[f]['added_clean'])

    lines[project].append(round(lines[project][0] / sum(lines[project]) * 100, 2))
for project in projects:
    tmp = [project, lines[project][0], lines[project][1],
           '{:<5.2f}% ({:6d} / {:<6d})'.format(lines[project][-1], lines[project][0],
                                               lines[project][0] + lines[project][1])]
    table.add_row(tmp)
    df_data.append(tmp)

table.add_row(['ALL', buggy, clean,
               '{:<5.2f}% ({:6d} / {:<6d})'.format(round(buggy * 100 / (buggy + clean), 2), clean, buggy + clean)])
df_data.append(['ALL', buggy, clean,
               '{:<5.2f}% ({:6d} / {:<6d})'.format(round(buggy * 100 / (buggy + clean), 2), clean, buggy + clean)])
print(table)
print(data.shape)
df = pd.DataFrame(df_data, columns=table.field_names)
# df.to_excel('./dataset_statistics_line_level_20220904.xlsx')
print(cnt)

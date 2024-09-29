import logging as root_logging
from pathlib import Path
import sys
from features.git import Git
from data.getMsg import getMsg
import json
import pandas as pd
import os
import pickle
import copy

# file_path ='/Users/sxz/Documents/coding/project/JITFine_data/data/fastjson_regression_bugs.pkl'  # sys.argv[1]
file_path = './data/all_regression_bugs.pkl'
def getLogger(log_file):
    # Set up the logger

    logger = root_logging.getLogger()
    logger.setLevel(root_logging.INFO)

    logger_format = root_logging.Formatter('%(asctime)s %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S')

    logging_file_handler = root_logging.FileHandler(log_file)
    logging_file_handler.setLevel(root_logging.INFO)
    logging_file_handler.setFormatter(logger_format)
    logger.addHandler(logging_file_handler)

    logging_stream_handler = root_logging.StreamHandler()
    logging_stream_handler.setLevel(root_logging.INFO)
    logging_stream_handler.setFormatter(logger_format)
    logger.addHandler(logging_stream_handler)

    logging = root_logging

    return logging


def main():
    data = pd.read_pickle(file_path)
    data.loc[:, 'msg'] = None
    print(data.shape, data.drop_duplicates().shape)
    projects = list(data['project_name'].drop_duplicates())
    adapter = Git(getLogger('./feature.log'))
    result = list()
    for project in projects:
        print('project:', project)
        commits_stat = {item['commit_hash']: item for item in adapter.log(project)}
        commits_msg = getMsg(project, data)
        assert len(commits_msg) <= len(commits_stat)
        for commit in commits_msg:
            tmp = [project]
            if commit[1] == '_':
                commits_stat[commit] = copy.deepcopy(commits_stat[commit[2:]])

            commits_stat[commit]['commit_message'] = commits_msg[commit]
            tmp.extend([commits_stat[commit][key] for key in commits_stat[commit].keys()])
            # append bug ids
            tmp.append(data[(data['project_name'] == project) & (data['commit_hash'] == commit)]['ID'].values[0])
            if commit[1] == '_':
                tmp[2] = commit
            result.append(tmp)
        # break
    return result


if __name__ == '__main__':
    ret = main()
    # 'commit_message', 'la', 'ld',  'nf', 'ns', 'nd', 'entropy', 'ndev', 'lt', 'nuc', 'age', 'exp', 'rexp', 'sexp', 'fix'
    columns = ['project', 'parent_hashes', 'commit_hash', 'author_name', 'author_email', 'author_date',
               'author_date_unix_timestamp', 'commit_message', 'la', 'ld', 'fileschanged', 'nf', 'ns', 'nd',
               'entropy', 'ndev', 'lt', 'nuc', 'age', 'exp', 'rexp', 'sexp', 'classification', 'fix', 'ID']
    data = pd.DataFrame(ret, columns=columns)
    # print(data)
    import os
    current_directory = os.getcwd()
    # project_path = os.path.join(current_directory,"JITFine_data",'data','all_changes_data')
    project_path = os.path.join(current_directory, 'data', 'all_changes_data')
    # 使用 pathlib.Path 来创建目录
    project_path = Path(project_path)

    if not project_path.exists():
        project_path.mkdir(parents=True, exist_ok=True)
    output_file = os.path.join(project_path, 'metrics.pkl')
    data.to_pickle(output_file)
    data.to_csv(os.path.join(project_path, 'metrics.csv'), index=False)
        # pickle.dump(data, open("./data/all_changes_data/metrics.pkl", "wb"), protocol=4)

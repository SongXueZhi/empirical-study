import logging as root_logging
import sys
from features.git import Git
from data.getMsg import getMsg
import json
import pandas as pd
import os
import pickle


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
            commits_stat[commit]['commit_message'] = commits_msg[commit]
            tmp.extend([commits_stat[commit][key] for key in commits_stat[commit].keys()])
            result.append(tmp)
        # break
    return result


if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print('only or not')
    else:
        print(sys.argv)
        buggy = sys.argv[1] == 'True'
        only_production_code = sys.argv[2] == 'True'
        all_data = dict()
        print('buggy' ,buggy, 'production',only_production_code)
        file_path = './data/all_changes_data/all_data.pkl' if only_production_code is False else './data/only_production_code/all_data_only_production_code.pkl'

        ret = main()
        # 'commit_message', 'la', 'ld',  'nf', 'ns', 'nd', 'entropy', 'ndev', 'lt', 'nuc', 'age', 'exp', 'rexp', 'sexp', 'fix'
        columns = ['project', 'parent_hashes', 'commit_hash', 'author_name', 'author_email', 'author_date',
                   'author_date_unix_timestamp', 'commit_message', 'la', 'ld', 'fileschanged', 'nf', 'ns', 'nd',
                   'entropy', 'ndev', 'lt', 'nuc', 'age', 'exp', 'rexp', 'sexp', 'classification', 'fix']
        data = pd.DataFrame(ret, columns=columns)
        # print(data)
        if only_production_code:
            data.to_pickle('./data/only_production_code/metrics_only_production_code.pkl')
        else:
            data.to_pickle('./data/all_changes_data/metrics.pkl')
            # pickle.dump(data, open("./data/all_changes_data/metrics.pkl", "wb"), protocol=4)

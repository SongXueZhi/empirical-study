import pandas as pd
import sys
import os
from pydriller import Git
import json


def main():
    data = pd.read_pickle(file_path)
    data.loc[:, 'msg'] = None
    print(data.shape, data.drop_duplicates().shape)
    projects = list(data['project_name'].drop_duplicates())
    print(projects, len(projects))
    all_msg = dict()
    for proj_name in projects:
        
        import os
        current_directory = os.getcwd()
        project_path = os.path.join(current_directory, 'repos', proj_name)
        gr = Git(project_path)
        
        commits = list(data[data['project_name'] == proj_name]['commit_hash'].drop_duplicates())
        print(proj_name, len(commits))
        tmp = dict()
        for commit_hash in commits:
            commit = gr.get_commit(commit_hash)
            if commit.merge:
                continue
            tmp[commit_hash] = commit.msg.split('git-svn-id')[0].strip()
        all_msg[proj_name] = tmp
        print(len(tmp))
    return all_msg


def getMsg(proj_name, data):
    current_directory = os.getcwd()
    projPath = os.path.join(current_directory, "JITFine_data", 'repos', proj_name)
    gr = Git(projPath)
    commits = list(data[data['project_name'] == proj_name]['commit_hash'].drop_duplicates())
    print(proj_name, len(commits))
    tmp = dict()
    for commit_hash in commits:
        commit = gr.get_commit(commit_hash)
        if commit.merge:
            continue
        tmp[commit_hash] = commit.msg.split('git-svn-id')[0].strip()

    return tmp

if __name__ == '__main__':
    # file_path = './only_production_code/all_data_only_production_code.pkl'
    # ret = main()
    # with open('./only_production_code/commit2msg.json', 'w') as f:
    #     json.dump(ret, f)
    with open('./only_production_code/commit2msg.json', 'r') as f:
        a = json.load(f)
    print(len(a), len(a['ant-ivy']))
    print((type(a)))

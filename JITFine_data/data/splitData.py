import pandas as pd
from sklearn.model_selection import train_test_split
from pydriller import Git
import pickle
from data.utils import java_filename_filter, check_line, check_change_line, preprocess_changes, split_sentence, \
    preprocess_code_line
from data.Dict import Dict
import os
import numpy as np
import pandas as pd


# 这个文件是主要的到code changes的文件
def get_train_test(metrics, all_changes):
    projects = metrics['project'].drop_duplicates().values
    projects = list(projects)
    train_set = pd.DataFrame()
    test_set = pd.DataFrame()
    valid_set = pd.DataFrame()
    cnt = 0
    for project in projects:
        # print('project: ', project)
        commits = metrics[metrics['project'] == project].reset_index(drop=True)
        changes = all_changes[all_changes['project'] == project].reset_index(drop=True)
        changes = changes[['commit_hash', 'is_buggy_commit']]
        commits = commits.sort_values(by=['author_date_unix_timestamp']).reset_index(drop=True)
        # print(commits.shape)
        commits = commits.merge(changes, on='commit_hash', how='left').drop_duplicates()
        cnt += commits.shape[0]
        # print(commits.shape)
        buggy_commits = commits[commits['is_buggy_commit'] == 1.0]
        clean_commits = commits[commits['is_buggy_commit'] != 1.0]

        # 不保证时间顺序
        # buggy_train = buggy_commits.sample(n=int(buggy_commits.shape[0] * 0.8), random_state=42)
        # buggy_valid = buggy_train.sample(n=int(buggy_train.shape[0] * 0.2), random_state=42)
        # buggy_test = buggy_commits[~buggy_commits['commit_hash'].isin(buggy_train['commit_hash'])]
        #
        # clean_train = clean_commits.sample(n=int(clean_commits.shape[0] * 0.8), random_state=42)
        # clean_valid = clean_train.sample(n=int(clean_train.shape[0] * 0.2), random_state=42)
        # clean_test = clean_commits[~clean_commits['commit_hash'].isin(clean_train['commit_hash'])]

        buggy_train = buggy_commits[:int(buggy_commits.shape[0] * 0.6)]
        buggy_valid = buggy_commits[int(buggy_commits.shape[0] * 0.6):int(buggy_commits.shape[0] * 0.8)]
        buggy_test = buggy_commits[int(buggy_commits.shape[0] * 0.8):]

        clean_train = clean_commits[:int(clean_commits.shape[0] * 0.6)]
        clean_valid = clean_commits[int(clean_commits.shape[0] * 0.6):int(clean_commits.shape[0] * 0.8)]
        clean_test = clean_commits[int(clean_commits.shape[0] * 0.8):]

        # divide valid from test 这种方式应该是不对的
        # buggy_valid = buggy_test.sample(n=int(buggy_test.shape[0] * 0.5), random_state=42)
        # buggy_test = buggy_test[~buggy_test['commit_hash'].isin(buggy_valid['commit_hash'])]
        # clean_valid = clean_test.sample(n=int(clean_test.shape[0] * 0.5), random_state=42)
        # clean_test = clean_test[~clean_test['commit_hash'].isin(clean_valid['commit_hash'])]
        # 最开始只有28划分
        # buggy_test_ = buggy_test
        # buggy_test = buggy_test_[:int(buggy_test_.shape[0] * 0.8)]
        # buggy_valid = buggy_test_[int(buggy_test_.shape[0] * 0.8):]
        # clean_train_ = clean_train
        # clean_train = clean_train_[:int(clean_train_.shape[0] * 0.8)]
        # clean_valid = clean_train_[int(clean_train_.shape[0] * 0.8):]

        commits_train = pd.concat([buggy_train, clean_train])
        commits_test = pd.concat([buggy_test, clean_test])
        commits_valid = pd.concat([buggy_valid, clean_valid])
        train_set = pd.concat([train_set, commits_train])
        valid_set = pd.concat([valid_set, commits_valid])
        test_set = pd.concat([test_set, commits_test])

        # break
    print(cnt)
    print(train_set.shape, valid_set.shape, test_set.shape)
    # return
    train_set = train_set.reset_index(drop=True)
    valid_set = valid_set.reset_index(drop=True)

    test_set = test_set.reset_index(drop=True)
    return train_set, valid_set, test_set


def get_changes(all_changes, commits):
    changes = pd.DataFrame(commits, columns=['commit_hash'])
    changes = changes.merge(all_changes, on='commit_hash', how='left')
    print(changes.shape, all_changes.shape)
    return changes


def get_JITFine():
    # 一开始没有从train中划分valid，如果直接train_test_split会导致训练和验证不符合time-aware
    metrics_file = './data/all_changes_data/metrics.pkl'
    changes_file = './data/all_changes_data/all_data.pkl'
    metrics = pd.read_pickle(metrics_file)
    all_changes = pd.read_pickle(changes_file)
    print(all_changes.shape)
    commits = all_changes[['project_name', 'commit_hash', 'is_buggy_commit']].drop_duplicates().reset_index(drop=True)
    commits.columns = ['project', 'commit_hash', 'is_buggy_commit']
    print(commits.shape, commits.shape[0] * 0.6, commits.shape[0] * 0.2, commits.shape[0] * 0.2,
          (commits.shape[0] * 0.6 + commits.shape[0] * 0.2 + commits.shape[0] * 0.2))
    # print(metrics)

    train_set, valid_set, test_set = get_train_test(metrics, commits)

    train_changes = get_changes(all_changes, train_set['commit_hash'])
    valid_changes = get_changes(all_changes, valid_set['commit_hash'])
    test_changes = get_changes(all_changes, test_set['commit_hash'])

    train_changes['changed_line'] = train_changes['changed_line'].apply(lambda x: split_sentence(x.strip()))
    valid_changes['changed_line'] = valid_changes['changed_line'].apply(lambda x: split_sentence(x.strip()))
    test_changes['changed_line'] = test_changes['changed_line'].apply(lambda x: split_sentence(x.strip()))

    train_set['commit_message'] = train_set['commit_message'].apply(lambda x: split_sentence(x.strip()))
    valid_set['commit_message'] = valid_set['commit_message'].apply(lambda x: split_sentence(x.strip()))
    test_set['commit_message'] = test_set['commit_message'].apply(lambda x: split_sentence(x.strip()))
    # tmp = pd.concat([train_changes, valid_changes])
    # print(tmp)
    # test(test_changes)
    # test(test_changes, 'jitline')
    get_complete_buggy_line_leve_file(test_changes)
    # get_ngram_data(pd.concat([train_changes,valid_changes]), mode='train')
    # get_ngram_data(train_changes, mode='train')
    # get_ngram_data(test_changes, mode='test')
    # return
    train_set.to_pickle('./data/JITFine/features_train.pkl')
    valid_set.to_pickle('./data/JITFine/features_valid.pkl')
    test_set.to_pickle('./data/JITFine/features_test.pkl')

    test_changes = format_changes(test_changes, test_set)
    pickle.dump(test_changes, open('./data/JITFine/changes_test_list.pkl', 'wb'))

    valid_changes = format_changes(valid_changes, valid_set)
    pickle.dump(valid_changes, open('./data/JITFine/changes_valid_list.pkl', 'wb'))

    train_changes = format_changes(train_changes, train_set)
    pickle.dump(train_changes, open('./data/JITFine/changes_train_list.pkl', 'wb'))
    # train_changes.to_pickle('./data/JITFine/changes_train.pkl')
    # valid_changes.to_pickle('./data/JITFine/changes_valid.pkl')
    # test_changes.to_pickle('./data/JITFine/changes_test.pkl')


def get_complete_buggy_line_leve_file(changes_data):
    # filepath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl'
    # data = pd.read_pickle(filepath)
    # data.columns = ['commit_hash', 'idx', 'changed_type', 'is_buggy_line', 'raw_changed_line',
    #                 'code_change_remove_common_tokens']
    # # data.to_pickle('/data1/kaiwenyang/JITFine/dataset/jitline/ww_format/changes_complete_buggy_line_level.pkl')
    newpath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset'

    # jitline,jitfine
    data = pickle.load(open(newpath + '/changes_test.pkl', 'rb'))
    commit_ids = data[0]
    labels = data[1]
    codes = data[-1]
    complete_buggy_line = []
    for commit_id, label, file_codes in zip(commit_ids, labels, codes):
        if label == 0:
            continue
        changes = changes_data[changes_data['commit_hash'] == commit_id]
        added_cnt = len(file_codes['added_code'])
        for idx, line in enumerate(file_codes['added_code']):
            tmp = changes[(changes['changed_type'] == 'added') & (changes['changed_line'] == line)]
            assert not tmp.empty
            labels = tmp['is_buggy_line'].unique()
            label = max(labels)
            complete_buggy_line.append([commit_id, idx, 'added', label, line, preprocess_code_line(line)])

        for idx, line in enumerate(file_codes['removed_code']):
            line = line.strip()
            tmp = changes[(changes['changed_type'] == 'deleted') & (changes['changed_line'] == line)]
            assert not tmp.empty
            labels = tmp['is_buggy_line'].unique()
            label = max(labels)
            complete_buggy_line.append(
                [commit_id, idx + added_cnt, 'deleted', label, line, preprocess_code_line(line)])

        # break
    complete_buggy_line = pd.DataFrame(complete_buggy_line,
                                       columns=['commit_id', 'idx', 'changed_type', 'label', 'raw_changed_line',
                                                'changed_line'])
    complete_buggy_line.to_pickle(
        '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl')


def test():
    filepath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl'
    changes_data = pd.read_pickle(filepath)
    commits = changes_data['commit_id'].unique()
    for commit in commits:
        tmp = changes_data[changes_data['commit_id'] == commit]
        assert any(tmp['label'].tolist())
        print(any(tmp['label'].tolist()))


def get_ngram_data(changes_data, mode='train'):
    if mode == 'train':
        newpath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset'
        data = pickle.load(open(newpath + '/changes_train.pkl', 'rb'))
        data2 = pickle.load(open(newpath + '/changes_valid.pkl', 'rb'))
        commit_ids = data[0] + data2[0]
        codes = data[-1] + data2[-1]
        # commit_ids = data[0]
        # codes = data[-1]
        all_clean_lines = []
        all_commits = []
        # train data
        for commit_id, file_codes in zip(commit_ids, codes):
            changes = changes_data[changes_data['commit_hash'] == commit_id]
            for idx, line in enumerate(file_codes['added_code']):
                tmp = changes[(changes['changed_type'] == 'added') & (changes['changed_line'] == line)]
                assert not tmp.empty
                labels = tmp['is_buggy_line'].unique()
                label = max(labels)
                if label == 0:
                    all_clean_lines.append(line)

        # test data

        # break
        code_str = '\n'.join(all_clean_lines)
        code_str = code_str.lower()
        # '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/saved_models_concat/new_dataset'
        base_data_dir = '/data1/kaiwenyang/JITFine/dataset/'
        data_for_ngram_dir = os.path.join(base_data_dir, 'ngram')
        if not os.path.exists(data_for_ngram_dir):
            os.makedirs(data_for_ngram_dir)
        with open(os.path.join(data_for_ngram_dir, 'train_data_with_valid.txt'), 'w') as f:
            f.write(code_str)
        # with open(os.path.join(data_for_ngram_dir, 'train_data.txt'), 'w') as f:
        #     f.write(code_str)
    else:
        filepath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl'
        all_code_lines = []
        all_commits = []
        all_ids = []
        all_labels = []
        data = pd.read_pickle(filepath)
        print(data.shape)
        data = data[data['changed_type'] == 'added']
        for idx, item in data.iterrows():
            commit_id, no_id, changed_type, label, raw_changed_line, changed_line = item
            all_code_lines.append(raw_changed_line)
            all_commits.append(commit_id)
            all_ids.append(str(no_id))
            all_labels.append(str(label))

        code_str = '\n'.join(all_code_lines)
        code_str = code_str.lower()
        commit_str = '\n'.join(all_commits)
        id_str = '\n'.join(all_ids)
        label_str = '\n'.join(all_labels)
        base_data_dir = '/data1/kaiwenyang/JITFine/dataset/'
        data_for_ngram_dir = os.path.join(base_data_dir, 'ngram')
        if not os.path.exists(data_for_ngram_dir):
            os.makedirs(data_for_ngram_dir)
        with open(os.path.join(data_for_ngram_dir, 'test_data_line_onlyadds.txt'), 'w') as f:
            f.write(code_str)
        with open(os.path.join(data_for_ngram_dir, 'test_data_commit_onlyadds.txt'), 'w') as f:
            f.write(commit_str)
        with open(os.path.join(data_for_ngram_dir, 'test_data_id_onlyadds.txt'), 'w') as f:
            f.write(id_str)
        with open(os.path.join(data_for_ngram_dir, 'test_data_label_onlyadds.txt'), 'w') as f:
            f.write(label_str)
        # with open(os.path.join(data_for_ngram_dir, 'test_data_line.txt'), 'w') as f:
        #     f.write(code_str)
        # with open(os.path.join(data_for_ngram_dir, 'test_data_commit.txt'), 'w') as f:
        #     f.write(commit_str)
        # with open(os.path.join(data_for_ngram_dir, 'test_data_id.txt'), 'w') as f:
        #     f.write(id_str)
        # with open(os.path.join(data_for_ngram_dir, 'test_data_label.txt'), 'w') as f:
        #     f.write(label_str)


def is_intersect():
    newpath = './data/JITFine/changes_test.pkl'
    new_train = os.path.join(newpath, 'changes_train.pkl')
    new_valid = os.path.join(newpath, 'changes_valid.pkl')
    new_test = os.path.join(newpath, 'changes_test.pkl')

    new_train = pickle.load(open(new_train, 'rb'))
    new_valid = pickle.load(open(new_valid, 'rb'))
    new_test = pickle.load(open(new_test, 'rb'))
    #
    train_commits = set(new_train[0])
    valid_commits = set(new_valid[0])
    test_commits = set(new_test[0])
    # new_train = pd.read_pickle(new_train)
    # new_valid = pd.read_pickle(new_valid)
    # new_test = pd.read_pickle(new_test)
    # train_commits=set(new_train['commit_hash'].unique())
    # valid_commits = set(new_valid['commit_hash'].unique())
    # test_commits = set(new_test['commit_hash'].unique())
    print(len(train_commits), len(valid_commits), len(test_commits))
    print(len(train_commits & valid_commits))
    print(len(train_commits & test_commits))
    print(len(valid_commits & test_commits))


def format_changes(changes_data, features_df):
    data = []
    df = features_df
    # print(type(df))  # list
    # print(len(df))  # 4
    # print(df.info())
    # commit, label, msg, code
    # commit hash
    # print(df.columns)
    commit_hash_list = df[['commit_hash', 'commit_message', 'is_buggy_commit']].drop_duplicates().reset_index()
    all_commits = []
    all_labels = []
    all_msgs = []
    all_codes = []
    commit_hash_list = commit_hash_list.to_numpy()
    # print(commit_hash_list)
    for idx, commit_hash, msg, label in commit_hash_list:
        print(idx)
        # add delete:
        dic = dict()
        # add
        cur_add_df = changes_data[
            (changes_data['commit_hash'] == commit_hash) & (changes_data['changed_type'] == 'added')]
        cur_add_list = set(cur_add_df["changed_line"])
        dic["added_code"] = list(cur_add_list)
        # del
        cur_del_df = changes_data[
            (changes_data['commit_hash'] == commit_hash) & (changes_data['changed_type'] == 'deleted')]
        cur_del_list = set(cur_del_df["changed_line"])
        dic["removed_code"] = list(cur_del_list)

        all_commits.append(commit_hash)
        all_labels.append(label)
        all_msgs.append(msg)
        all_codes.append(dic)

    return [all_commits, all_labels, all_msgs, all_codes]


def get_deepjit_cc2vec_1(filepath, return_projects=False):
    # 这个版本用到了pydriller，后来觉得直接通过jitfine数据集构建更好，这样肯定公平点
    # deepJIT & cc2vec
    # train_set = pd.read_pickle('./data/JITFine/features_train.pkl')
    # test_set = pd.read_pickle('./data/JITFine/features_test.pkl')
    # train_changes = pd.read_pickle('./data/JITFine/changes_train.pkl')
    # test_changes = pd.read_pickle('./data/JITFine/changes_test.pkl')
    data = pd.read_pickle(filepath)[['project', 'commit_hash', 'is_buggy_commit', 'commit_message']]
    project_list = data['project'].drop_duplicates()
    ids, labels, msgs, codes, deepjit_codes, deepjit_raw_codes, history, k_feature = [], [], [], [], [], [], [], []
    projects = []
    # print(len(project_list))
    for project in project_list:
        import os
        current_directory = os.getcwd()
        project_path = os.path.join(current_directory, 'repos', project)
        gr = Git(project_path)
        project_data = data[data['project'] == project]
        print(f'project: {project} has {project_data.shape[0]} items')
        for _, (project, commit_hash, label, msg) in project_data.iterrows():
            commit = gr.get_commit(commit_hash)

            msg = msg.strip()
            msg = split_sentence(msg)
            msg = ' '.join(msg.split(' ')).lower()

            format_code = []
            files_code = []
            raw_code = []
            modified_files = [file for file in commit.modified_files if java_filename_filter(file.new_path if
                                                                                             file.new_path else file.old_path)]
            # 因为是从JITFine数据集来的所以一定有java文件
            assert len(modified_files)
            for file in modified_files:

                diff = file.diff_parsed
                added_code, removed_code, file_codes = [], [], []
                # print(diff)

                # 移除注释
                adds_origin = [line for no, line in
                               file.diff_parsed['added'] if len(line)]
                adds_lines_no = [no for no, line in
                                 file.diff_parsed['added'] if len(line)]
                deletes_origin = [line for no, line in
                                  file.diff_parsed['deleted'] if len(line)]
                deletes_lines_no = [no for no, line in
                                    file.diff_parsed['deleted'] if len(line)]
                # print(adds_origin)
                if len(adds_origin):
                    source_code = file.source_code.replace(r'\r', '').split('\n')
                    source_code = check_line(source_code, 0)
                    adds_origin = preprocess_changes(adds_origin,
                                                     source_code, adds_lines_no)
                if len(deletes_origin):
                    source_code_before = file.source_code_before.replace(r'\r', '').split('\n')
                    source_code_before = check_line(source_code_before, 0)
                    deletes_origin = preprocess_changes(deletes_origin, source_code_before, deletes_lines_no)

                for line_no, code in deletes_origin:
                    remove_code = code.strip()
                    # print(remove_code)
                    remove_code = ' '.join(split_sentence(remove_code).split())
                    # print(remove_code)
                    remove_code = ' '.join(remove_code.split(' '))
                    # print(remove_code)
                    # remove_code = 'added _ code removed _ code'
                    removed_code.append(remove_code)
                    file_codes.append((line_no, remove_code))
                    if len(removed_code) > 10: break

                for line_no, code in adds_origin:
                    # if len(diff['b'][line]['code'].split()) > 3:
                    add_code = code.strip()
                    # print(add_code)
                    add_code = ' '.join(split_sentence(add_code).split())
                    # print(add_code)
                    add_code = ' '.join(add_code.split(' '))
                    # print(add_code)
                    # add_code = 'added _ code removed _ code'
                    added_code.append(add_code)
                    file_codes.append((line_no, add_code))
                    if len(added_code) > 10: break

                file_codes.sort(key=lambda x: x[0])
                raw_code.extend([code[1] for code in file_codes])
                raw_code = raw_code[:10]
                format_code.append("added _ code removed _ code")
                files_code.append({'added_code': added_code, 'removed_code': removed_code})
                # shuffle(code)

                if len(format_code) == 10: break
            ids.append(commit_hash)
            labels.append(label)
            msgs.append(msg)
            deepjit_codes.append(format_code)
            deepjit_raw_codes.append(raw_code)
            codes.append(files_code)
            projects.append(project)
    deepjit_raw_data = [ids, labels, msgs, deepjit_raw_codes]
    deepjit_data = [ids, labels, msgs, deepjit_codes]
    print('Data size: {}, Bug size: {}'.format(
        len(labels), sum(labels)))
    cc2vec_data = [ids, labels, msgs, codes]

    if return_projects:
        return deepjit_data, deepjit_raw_data, cc2vec_data, projects
    return deepjit_data, deepjit_raw_data, cc2vec_data, None


def get_deepjit_cc2vec(changes_path, features_path, allchanges_path, return_projects=False):
    # deepJIT & cc2vec
    # data = all_changes
    changes_data = pickle.load(open(changes_path, 'rb'))
    features_data = pd.read_pickle(features_path)
    print(len(changes_data))
    # jitfine dataset
    data = pd.read_pickle(allchanges_path)
    all_commits, all_labels, all_msgs, all_codes = changes_data
    # print(all_commits)
    ids, labels, msgs, codes, deepjit_codes, deepjit_raw_codes, history, k_feature = [], [], [], [], [], [], [], []
    projects = []
    for commit, label, msg in zip(all_commits, all_labels, all_msgs):
        # print(commit)
        all_changes = data[data['commit_hash'] == commit]
        all_files = all_changes['file_path'].unique()

        msg = msg.strip()
        msg = split_sentence(msg)
        msg = ' '.join(msg.split(' ')).lower()

        format_code = []
        files_code = []
        raw_code = []
        for file in all_files:
            added_code, removed_code, file_codes = [], [], []
            all_added_code = \
                all_changes[(all_changes['changed_type'] == 'added') & (all_changes['file_path'] == file)][
                    'changed_line'].tolist()
            all_removed_code = \
                all_changes[(all_changes['changed_type'] == 'deleted') & (all_changes['file_path'] == file)][
                    'changed_line'].tolist()
            # print(file, len(all_added_code), len(all_removed_code))
            # print(adds_origin)
            for line_no, code in enumerate(all_removed_code):
                remove_code = code.strip()
                # print(remove_code)
                remove_code = ' '.join(split_sentence(remove_code).split())
                # print(remove_code)
                remove_code = ' '.join(remove_code.split(' '))
                # print(remove_code)
                # remove_code = 'added _ code removed _ code'
                removed_code.append(remove_code)
                file_codes.append((line_no, remove_code))
                if len(removed_code) > 10: break

            for line_no, code in enumerate(all_added_code):
                # if len(diff['b'][line]['code'].split()) > 3:
                add_code = code.strip()
                # print(add_code)
                add_code = ' '.join(split_sentence(add_code).split())
                # print(add_code)
                add_code = ' '.join(add_code.split(' '))
                # print(add_code)
                # add_code = 'added _ code removed _ code'
                added_code.append(add_code)
                file_codes.append((line_no, add_code))
                if len(added_code) > 10: break

            file_codes.sort(key=lambda x: x[0])
            raw_code.extend([code[1] for code in file_codes])
            raw_code = raw_code[:10]
            format_code.append("added _ code removed _ code")
            files_code.append({'added_code': added_code, 'removed_code': removed_code})
            # shuffle(code)

            if len(format_code) == 10: break
        ids.append(commit)
        labels.append(label)
        msgs.append(msg)
        deepjit_codes.append(format_code)
        deepjit_raw_codes.append(raw_code)
        codes.append(files_code)
        # projects.append(project)
    deepjit_raw_data = [ids, labels, msgs, deepjit_raw_codes]
    deepjit_data = [ids, labels, msgs, deepjit_codes]
    print('Data size: {}, Bug size: {}'.format(
        len(labels), sum(labels)))
    cc2vec_data = [ids, labels, msgs, codes]

    if return_projects:
        return deepjit_data, deepjit_raw_data, cc2vec_data, projects
    return deepjit_data, deepjit_raw_data, cc2vec_data, None


def get_baseline():
    # deepJIT & cc2vec
    #
    deepjit_train_data, deepjit_train_raw_data, cc2vec_train_data, projects_train = get_deepjit_cc2vec(
        './data/JITFine/changes_train.pkl', './data/JITFine/features_train.pkl', './data/all_changes_data/all_data.pkl',
        False)
    # valid?
    deepjit_test_data, deepjit_test_raw_data, cc2vec_test_data, projects_test = get_deepjit_cc2vec(
        './data/JITFine/changes_test.pkl', './data/JITFine/features_test.pkl', './data/all_changes_data/all_data.pkl',
        False)

    with open('./data/deepjit/train_data.pkl', 'wb') as f:
        pickle.dump(deepjit_train_raw_data, f)
    with open('./data/deepjit/test_data.pkl', 'wb') as f:
        pickle.dump(deepjit_test_raw_data, f)
    with open('./data/deepjit/projects_train.pkl', 'wb') as f:
        pickle.dump(projects_train, f)
    with open('./data/deepjit/projects_test.pkl', 'wb') as f:
        pickle.dump(projects_test, f)
    #
    with open('./data/cc2vec/train_data.pkl', 'wb') as f:
        pickle.dump(cc2vec_train_data, f)
    with open('./data/cc2vec/test_data.pkl', 'wb') as f:
        pickle.dump(cc2vec_test_data, f)
    with open('./data/cc2vec/projects_train.pkl', 'wb') as f:
        pickle.dump(projects_train, f)
    with open('./data/cc2vec/projects_test.pkl', 'wb') as f:
        pickle.dump(projects_test, f)

    # with open('./data/deepjit/train_data.pkl', 'rb') as f:
    #     deepjit_train_raw_data = pickle.load(f)
    # with open('./data/deepjit/test_data.pkl', 'rb') as f:
    #     deepjit_test_raw_data = pickle.load(f)
    # with open('./data/cc2vec/train_data.pkl', 'rb') as f:
    #     cc2vec_train_data = pickle.load(f)
    # with open('./data/cc2vec/test_data.pkl', 'rb') as f:
    #     cc2vec_test_data = pickle.load(f)
    deepjit_dict = get_deepjit_dict(deepjit_train_raw_data)
    pickle.dump(deepjit_dict, open("./data/cc2vec/dataset_dict.pkl", 'wb'))
    cc2vec_dict = get_cc2vec_dict(cc2vec_train_data)
    pickle.dump(cc2vec_dict, open("./data/deepjit/dataset_dict.pkl", 'wb'))
    # return cc2vec_train_data


def get_deepjit_dict(train_set, test_set=None):
    codes = (train_set[-1] + test_set[-1]) if test_set is not None else train_set[-1]
    msgs = (train_set[-2] + test_set[-2]) if test_set is not None else train_set[-2]
    msg_dict = Dict(lower=True)
    code_dict = Dict(lower=True)
    # code_dict
    for code_list in codes:
        for code in code_list:
            for word in code.split():
                code_dict.add(word)

    # msg_dict
    for msg in msgs:
        for word in msg.split():
            msg_dict.add(word)

    msg_dict = msg_dict.prune(100000)
    code_dict = code_dict.prune(100000)
    print(f'msg_dict size:{msg_dict.size()}, code_dict size:{code_dict.size()}')
    dataset_dict = [msg_dict.get_dict(), code_dict.get_dict()]
    return dataset_dict


def get_cc2vec_dict(train_set, test_set=None):
    codes = train_set[-1] + test_set[-1] if test_set else train_set[-1]
    msgs = train_set[-2] + test_set[-2] if test_set else train_set[-2]
    msg_dict = Dict(lower=True)
    code_dict = Dict(lower=True)
    # code_dict
    for files in codes:
        # print(files)
        for code_changes in files:
            for code in code_changes['added_code']:
                for word in code.split():
                    code_dict.add(word)
            for code in code_changes['removed_code']:
                for word in code.split():
                    code_dict.add(word)

    # code_dict
    for msg in msgs:
        for word in msg.split():
            msg_dict.add(word)

    msg_dict = msg_dict.prune(100000)
    code_dict = code_dict.prune(100000)
    # print(code_dict.get_dict())
    # print(msg_dict.get_dict())
    print(f'msg_dict size:{msg_dict.size()}, code_dict size:{code_dict.size()}')
    dataset_dict = [msg_dict.get_dict(), code_dict.get_dict()]
    return dataset_dict


# 旧版，根据所有的change
def get_jitline_dict0(train_set, train_changes, test_set=None, test_changes=None):
    # deepJIT & cc2vec
    train_changes = train_changes[['commit_hash', 'changed_line']]
    if test_changes:
        test_changes = test_changes[['commit_hash', 'changed_line']]
        train_changes = pd.concat([train_changes, test_changes])
    train_set = train_set[['commit_hash', 'commit_message']]
    if test_set:
        test_set = test_set[['commit_hash', 'commit_message']]
        train_set = pd.concat([train_set, test_set])
    msg_dict = Dict(lower=True)
    code_dict = Dict(lower=True)
    # msg_dict
    for idx, item in train_set.iterrows():
        for word in item['commit_message'].split():
            msg_dict.add(word)

    # code_dict
    train_changes.loc[:, 'changed_line'] = train_changes.loc[:, 'changed_line'].apply(lambda x: preprocess_code_line(x))
    for idx, item in train_changes.iterrows():
        for word in item['changed_line'].split():
            code_dict.add(word)
    msg_dict = msg_dict.prune(100000)
    code_dict = code_dict.prune(100000)
    print(f'msg_dict size:{msg_dict.size()}, code_dict size:{code_dict.size()}')
    dataset_dict = [msg_dict.get_dict(), code_dict.get_dict()]
    return dataset_dict


# 根据deepjit数据获得
def get_jitline_dict(train_set, test_set=None):
    codes = train_set[-1] + test_set[-1] if test_set else train_set[-1]
    msgs = train_set[-2] + test_set[-2] if test_set else train_set[-2]
    msg_dict = Dict(lower=True)
    code_dict = Dict(lower=True)
    # code_dict
    # preprocessing code according to jitline paper
    new_codes = []
    for files in codes:
        new_files = []
        for code_changes in files:
            new_code_changes = {'added_code': [], 'removed_code': []}
            for code in code_changes['added_code']:
                code = preprocess_code_line(code)
                new_code_changes['added_code'].append(code)
            for code in code_changes['removed_code']:
                code = preprocess_code_line(code)
                new_code_changes['removed_code'].append(code)
        new_files.append(new_code_changes)
    train_set[-1] = new_codes
    for files in new_codes:
        # print(files)
        for code_changes in files:
            for code in code_changes['added_code']:
                for word in code.split():
                    code_dict.add(word)
            for code in code_changes['removed_code']:
                for word in code.split():
                    code_dict.add(word)

    # code_dict
    for msg in msgs:
        for word in msg.split():
            msg_dict.add(word)

    msg_dict = msg_dict.prune(100000)
    code_dict = code_dict.prune(100000)
    # print(code_dict.get_dict())
    # print(msg_dict.get_dict())
    print(f'msg_dict size:{msg_dict.size()}, code_dict size:{code_dict.size()}')
    dataset_dict = [msg_dict.get_dict(), code_dict.get_dict()]
    return dataset_dict, train_set


def get_JITLine():
    # get_jitline_dict('./data/JITFine/changes_train.pkl')

    # train_set = pd.read_pickle('./data/JITFine/features_train.pkl')
    # test_set = pd.read_pickle('./data/JITFine/features_test.pkl')
    # train_changes = pd.read_pickle('./data/JITFine/changes_train.pkl')
    # test_changes = pd.read_pickle('./data/JITFine/changes_test.pkl')
    # dataset_dict = get_jitline_dict(train_set, train_changes)
    # pickle.dump(dataset_dict, open("./data/jitline/dataset_dict.pkl", 'wb'))
    # 根据jitline的代码和实验结果推断，训练的数据是来自deepjit的

    train_set = pd.read_pickle('./data/deepjit/train_data.pkl')
    dataset_dict, train_changes = get_jitline_dict(train_set)
    test_set = pd.read_pickle('./data/deepjit/test_data.pkl')
    _, test_changes = get_jitline_dict(test_set)

    pickle.dump(dataset_dict, open("./data/jitline/dataset_dict.pkl", 'wb'))
    pickle.dump(dataset_dict, open("./data/jitline/changes_train.pkl", 'wb'))
    pickle.dump(dataset_dict, open("./data/jitline/changes_test.pkl", 'wb'))


def is_euqal():
    newpath = '/data1/kaiwenyang/JITFine_data/JITFine/data/JITFine'
    oldpath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format'
    new_train = os.path.join(newpath, 'changes_train.pkl')
    old_train = os.path.join(oldpath, 'changes_train.pkl')
    new_valid = os.path.join(newpath, 'changes_valid.pkl')
    old_valid = os.path.join(oldpath, 'changes_valid.pkl')

    new_train = pickle.load(open(new_train, 'rb'))
    new_valid = pickle.load(open(new_valid, 'rb'))
    old_train = pickle.load(open(old_train, 'rb'))
    old_valid = pickle.load(open(old_valid, 'rb'))

    old_commits = set(list(old_train[0]) + list(old_valid[0]))
    new_commits = set(list(new_train[0]) + list(new_valid[0]))
    diff = set(old_commits) - set(new_commits)
    for commit in old_commits:
        assert commit in new_commits
    print(len(old_commits), len(new_commits))
    print(diff)


def main():
    get_JITFine()
    # test()
    # get_ngram_data()
    # 验证一下重新划分的是train+valid是否等于原来的train
    # is_euqal()
    # is_intersect()
    # get_baseline()
    # get_JITLine()

    # test()


if __name__ == '__main__':
    main()

import pickle

import pandas as pd

# from data.utils import preprocess_code_line


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


if __name__ == '__main__':
    a = pickle.load(open('/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_train.pkl', 'rb'))
    b = pickle.load(open('/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_test.pkl', 'rb'))
    c = pickle.load(open('/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_valid.pkl', 'rb'))
    # print(a.shape, b.shape, c.shape)
    print(len(a[0]))
    complete_buggy_line = pd.read_pickle('/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl')
    print(complete_buggy_line.columns)
    print(complete_buggy_line['changed_type'])

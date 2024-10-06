import pickle

import pandas as pd
import os
from utils import preprocess_code_line


def get_complete_buggy_line_leve_file():
    # filepath = '/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl'
    # data = pd.read_pickle(filepath)
    # data.columns = ['commit_hash', 'idx', 'changed_type', 'is_buggy_line', 'raw_changed_line',
    #                 'code_change_remove_common_tokens']
    # # data.to_pickle('/data1/kaiwenyang/JITFine/dataset/jitline/ww_format/changes_complete_buggy_line_level.pkl')
    # newpath = os.path.join(os.getcwd(),'JITFine_data', 'data')
    newpath = os.path.join(os.getcwd())

    # jitline,jitfine
    data = pickle.load(open(newpath + '/changes_reg_test.pkl', 'rb'))
    commit_ids = data[0]
    labels = data[1]
    codes = data[-1]
    complete_buggy_line = []
    for commit_id, label, file_codes in zip(commit_ids, labels, codes):
        if label == 0:
            continue
        added_cnt = len(file_codes['added_code'])
        for idx, line in enumerate(file_codes['added_code']):
            
            label = 1
            complete_buggy_line.append([commit_id, idx, 'added', label, line, preprocess_code_line(line)])

        for idx, line in enumerate(file_codes['removed_code']):
    
            label = 1
            complete_buggy_line.append(
                [commit_id, idx + added_cnt, 'deleted', label, line, preprocess_code_line(line)])

        # break
    complete_buggy_line = pd.DataFrame(complete_buggy_line,
                                       columns=['commit_id', 'idx', 'changed_type', 'label', 'raw_changed_line',
                                                'changed_line'])
    complete_buggy_line.to_pickle(os.path.join(newpath, 'complete_buggy_line.pkl'))



if __name__ == '__main__':
    
    # changes_test = pd.read_pickle(os.path.join(os.getcwd(), 'JITFine_data','data', 'changes_test.pkl'))            
    get_complete_buggy_line_leve_file()
    # print(a.shape, b.shape, c.shape)
    # print(len(a[0]))
    # complete_buggy_line = pd.read_pickle('/data1/kaiwenyang/JITFine/dataset/jitfine/ww_format/new_dataset/changes_complete_buggy_line_level.pkl')
    # print(complete_buggy_line.columns)
    # print(complete_buggy_line['changed_type'])

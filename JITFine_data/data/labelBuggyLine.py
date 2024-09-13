from pydriller import Git
import pandas as pd
import json
import re


# from data.utils import java_filename_filter, check_line


def preprocess_changes(changes, source_code):
    changes = [line.strip() for line in changes]
    print('in preprocess_changes')
    changes = [line for line in changes if line in source_code and len(line)]
    return changes


def main(buggy_commits_file, buggy_changes_file):
    with open(buggy_commits_file, 'r') as f:
        buggy_commits = json.load(f)
    with open(buggy_changes_file, 'r') as f:
        buggy_changes = json.load(f)
    all_changes = dict()
    buggy_cnt = 0
    outlier_cnt = 0
    all_cnt = 0
    # print(buggy_commits.keys())
    # return

    for no, proj_name in enumerate(buggy_commits.keys()):
        # print(list(buggy_changes.keys())[no])
        assert proj_name == list(buggy_changes.keys())[no]
        print('project:', proj_name)
        all_changes[proj_name] = dict()
        import os
        current_directory = os.getcwd()
        project_path = os.path.join(current_directory, 'repos', proj_name)
        gr = Git(project_path)
        bug_inducing_changes = buggy_changes[proj_name]
        bug_inducing_commits = buggy_commits[proj_name]
        print('commits_in_changes: ', len(bug_inducing_changes.keys()), '\ncommits_in_blame: ',
              len(bug_inducing_commits.keys()))
        assert len(bug_inducing_changes.keys()) <= len(bug_inducing_commits.keys())
        for commit in bug_inducing_changes.keys():  # 不用bug inducing commits因为在收集changes时会过滤掉一些outlier
            added = bug_inducing_changes[commit]['added']
            deleted = bug_inducing_changes[commit]['deleted']
            bug_inducing_changes[commit]['added_buggy_level'] = dict()
            for file in bug_inducing_commits[commit].keys():  # 只用bug inducing commits因为在收集changes时会引入一些其他file
                print(file)
                print(commit)
                print(added.keys())
                assert file in list(added.keys())
                file_buggy_lines = bug_inducing_commits[commit][file]
                tmp = {'added_buggy': list(), 'added_clean': list(), 'deleted': deleted[file]}
                added_lines = added[file]
                buggy_lines = set([file_buggy_lines[no] for no in file_buggy_lines])
                for add_line in added_lines:
                    add_line = add_line.replace(r'\\r', '').replace(r'\\t', '').replace(r'\r',
                                                                                        '').replace(
                        r'\t', '').strip()
                    if add_line in buggy_lines:
                        tmp['added_buggy'].append(add_line)
                    else:
                        tmp['added_clean'].append(add_line)
                outlier = [l for l in buggy_lines if l not in tmp['added_buggy']]
                outlier_cnt += len(outlier)
                print('buggy_line: ', len(set(buggy_lines)))
                print('outliers: ', len(outlier))
                print('added_buggy: ', len(tmp['added_buggy']), '\nadded_clean: ', len(tmp['added_clean']),
                      '\nadded_lines: ', len(added_lines))
                assert len(outlier) + len(tmp['added_buggy']) == len(buggy_lines)

                assert len(tmp['added_buggy']) + len(tmp['added_clean']) == len(added_lines)
                buggy_cnt += len(tmp['added_buggy'])
                all_cnt += len(added_lines)
                bug_inducing_changes[commit]['added_buggy_level'][file] = tmp
        all_changes[proj_name] = bug_inducing_changes

    return buggy_cnt, outlier_cnt, all_cnt, all_changes


if __name__ == '__main__':
    only_production_code = True

    if only_production_code:
        ret = main('./data/only_production_code/buggy_commits_only_production_code.json',
                   './data/only_production_code/buggy_changes_only_production_code.json')
        # print(ret)
        buggy_cnt, outlier_cnt, all_cnt, bug_inducing_changes = ret
        print(f'buggy_cnt_sum:{buggy_cnt}, outlier_cnt_sum:{outlier_cnt}, all_cnt_sum:{all_cnt}')
        with open('./data/only_production_code/buggy_changes_only_production_code_with_buggy_line.json', 'w') as f:
            json.dump(ret, f)
    else:
        ret = main('./data/all_changes_data/buggy_commits.json', './data/all_changes_data/buggy_changes.json')
        buggy_cnt, outlier_cnt, all_cnt, bug_inducing_changes = ret
        print(f'buggy_cnt_sum:{buggy_cnt}, outlier_cnt_sum:{outlier_cnt}, all_cnt_sum:{all_cnt}')
        with open('./data/all_changes_data/buggy_changes_with_buggy_line.json', 'w') as f:
            json.dump(ret, f)

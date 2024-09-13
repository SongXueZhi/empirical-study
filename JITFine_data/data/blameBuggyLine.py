import re
import os
import subprocess
from pathlib import Path
import json
import re
import pandas as pd
from data.utils import java_filename_filter


def gitAnnotate(repo_data, repo_name):
    """
    tracks down the origin of the deleted/modified loc in the regions dict using
    the git annotate (now called git blame) feature of git and a list of commit
    hashes of the most recent revision in which the line identified by the regions
    was modified. these discovered commits are identified as bug-introducing changes.

    git blame command is set up to start looking back starting from the commit BEFORE the
    commit that was passed in. this is because a bug MUST have occured prior to this commit.

    @regions - a dict of {file} -> {list of line numbers that were modified}
    @commit - commit that belongs to the passed in chucks/regions.
    """
    bug_introducing_changes = dict()
    mode_cnt = dict()
    before_cnt = 0
    error_cnt = 0
    no_java_cnt = 0
    no_core_cnt = 0
    for idx, item in repo_data.iterrows():
        repo_name, commit, lines_label, file, mode, old_file, _, _, old_start, old_lines, content, _, _, lines_manual = item.values
        if not java_filename_filter(old_file if old_file != '' else file, production_only=only_production_code):
            no_java_cnt += 1
            continue
        if mode in mode_cnt:
            mode_cnt[mode] += 1
        else:
            mode_cnt[mode] = 1
        if old_lines == 0 or mode == 'A':
            continue
        # content find delete lines
        bugfix_no = lines_label['bugfix']
        old_lines = dict()
        bugfix_delete_lines = list()
        print(lines_label)
        print('bugfix_no: ', bugfix_no)
        print('content: \n', content)
        content = content.split('\n')

        # 找到数据bugfix的delete lines
        for no, line in enumerate(content):
            # print('line: ',len(line),line)
            if len(line) and line[0] != '+':
                old_lines[no] = line
                if no in bugfix_no:
                    bugfix_delete_lines.append(no)
                # no content中的行号
        print(old_lines)
        print(file)
        print(commit)
        print('old_start:', old_start)
        print(old_lines)
        for cnt, no in enumerate(old_lines.keys()):
            if no not in bugfix_delete_lines:
                continue
            if commit == '1e19372380cc2e3e420b31916e6c4bc3eebc8144' and file == 'src/java/org/apache/ivy/plugins/parser/xml/XmlModuleDescriptorUpdater.java':
                print(repr(old_lines[0]))
                # print(old_lines.values()[0])
                print('\\')
            line = repr(old_lines[no][1:])[1:-1].strip()
            line = line.replace(r'\\r', '').replace(r'\\t', '').replace(r'\r', '').replace(r'\t', '').strip()
            if commit == 'be8e6831821a9f315de1dae8608ea6acc55b0fc9' and file == 'src/java/org/apache/ivy/osgi/repo/AbstractFSManifestIterable.java':
                line = line.replace('>', '')

            print(no, line)
            # if line.encode('utf-8') == '{"\\u00F3", "&ograve;"}, // � - lowercase o, grave accent'.encode('utf-8'):
            #     continue
            line_no = str(old_start + cnt)
            print("git blame -L " + line_no + ",+1 -w " + commit + "^ -l -- '" \
                  + (old_file if old_file != '' else file) + "'")
            try:
                current_directory = os.getcwd()
                project_path = os.path.join(current_directory, 'repos', repo_name)
                ret = str(subprocess.check_output("git blame -L " + line_no + ",+1 -w " + commit + "^ -l -n -f -- '" \
                                                  + (old_file if old_file != '' else file) + "'", shell=True,
                                                  cwd=project_path))
                print(ret)
            except Exception as e:
                #             print(item)
                error_cnt += 1
                print('exception: ', e, mode)
                continue
                # break
            blamed_line = ''.join(ret[ret.index(')') + 1:])[:-3].replace(r'\\r', '').replace(r'\\t', '').replace(r'\r',
                                                                                                                 '').replace(
                r'\t', '').strip()
            old_line_no = int(ret.split(' ')[2])
            old_file_name = ret.split(' ')[1].strip()

            print('blamed line:', blamed_line)
            print('origin line:', line)
            # if old_file_name == 'src/java/fr/jayasoft/ivy/external/m2/PomModuleDescriptorParser.java':
            #     print(java_filename_filter(old_file_name, production_only=only_production_code))
            #     print('there:', old_file_name,
            #           java_filename_filter(old_file_name, production_only=only_production_code))
            if java_filename_filter(old_file_name, production_only=only_production_code) is False:
                print('blamed file not production_code')
                no_core_cnt += 1
                continue
            #  {"\\u00F3", "&ograve;"}, // � - lowercase o, grave accent
            # if blamed_line.encode('utf-8') == r'{"\\u00F3", "&ograve;"}, // \xf2 - lowercase o, grave accent':
            #     continue
            # if file not in ['src/main/java/org/apache/commons/lang3/text/translate/EntityArrays.java',
            #                 'src/main/java/org/apache/commons/validator/routines/DomainValidator.java']:
            #  d   assert blamed_line == line
            buggy_change = ret.split(" ")[0][2:]
            if buggy_change[0] == '^':
                before_cnt += 1
            if buggy_change not in bug_introducing_changes:
                bug_introducing_changes[buggy_change] = dict()
            if old_file_name not in bug_introducing_changes[buggy_change]:
                bug_introducing_changes[buggy_change][old_file_name] = dict()
            bug_introducing_changes[buggy_change][old_file_name][old_line_no] = blamed_line
    #         print(buggy_change)
    #
    # break
    print('buggy_commit_cnt: ', len(bug_introducing_changes))
    print('mode_cnt:', mode_cnt)
    print('error_cnt:', error_cnt)
    print('before_cnt:', before_cnt)
    print('no_java_cnt: ', no_java_cnt)
    print('no_java_cnt by blame: ', no_core_cnt)
    print(len(bug_introducing_changes))
    return bug_introducing_changes


def main():
    if only_consensus:
        contain_bugfix = data[data['lines_verified'].apply(lambda x: 'bugfix' in x)]
    else:
        def func(x):
            buggy_lines = list()
            for person_labels in x.values():
                if 'bugfix' in person_labels:
                    buggy_lines.extend(person_labels['bugfix'])
            buggy_lines = set(buggy_lines)
            return buggy_lines

        tmp = data['lines_manual'].apply(func)
        contain_bugfix = data[tmp.apply(lambda x: len(x) > 0)]
        contain_bugfix['lines_verified'] = tmp[tmp.apply(lambda x: len(x) > 0)].apply(lambda x: {'bugfix': list(x)})

    projects = contain_bugfix['project'].drop_duplicates().values
    print(projects)
    proj2inducing = dict()

    for name in projects:
        # name = 'commons-math'
        # if name != 'ant-ivy':
        #     continue
        # if name == 'wss4j' or name == 'santuario-java':
        #     continue
        if name != 'santuario-java':
            continue
        print('project: ', name)


        tmp = contain_bugfix[contain_bugfix['project'] == name]
        print(tmp)
        ret = gitAnnotate(tmp, name)
        proj2inducing[name] = ret
        # break
    return proj2inducing


if __name__ == '__main__':
    data = pd.read_json('~/JITFine/JITFine/data/hunk_labels.json')
    only_consensus = True
    only_production_code = False
    ret = main()
    # if only_production_code:
    #     with open('./data/only_production_code/buggy_commits_only_production_code.json', 'w') as f:
    #         json.dump(ret, f)
    # else:
    #     with open('./data/all_changes_data/buggy_commits.json', 'w') as f:
    #         json.dump(ret, f)

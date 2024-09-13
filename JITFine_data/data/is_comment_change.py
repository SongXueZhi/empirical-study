from pydriller import Git
import pandas as pd
import json
import re
from data.utils import java_filename_filter, check_line, check_change_line

def main():
    with open('./data/is_comment.json', 'r') as f:
        data = json.load(f)
    print(data)
    names = data.keys()
    for name in names:
        import os
        current_directory = os.getcwd()
        project_path = os.path.join(current_directory, 'repos', name)
        gr = Git(project_path)
        for commit_hash in data[name]:
            commit = gr.get_commit(commit_hash)
            for file in commit.modified_files:
                adds_origin = [line for no, line in
                               file.diff_parsed['added'] if len(line)]
                if len(adds_origin):
                    source_code = file.source_code.replace(r'\r', '').split('\n')
                    source_code = check_line(source_code, 0)
                    print('abcd')
                    adds_origin = check_change_line(adds_origin)
                is_ = [l in source_code for l in adds_origin]
                print(is_)
                print(adds_origin)
                # print(source_code)
                # print(file.new_path)
                if adds_origin[0] != 'Bundle-DocURL: http://ant.apache.org/ivy/':
                    print(name, commit_hash)
                    assert any(is_) is False


if __name__ == '__main__':
    main()
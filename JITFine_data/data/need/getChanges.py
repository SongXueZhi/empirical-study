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
            java_file = [java_filename_filter(file.new_path if
                                              file.new_path else file.old_path,
                                              production_only=False) for file in
                         commit.modified_files]
            for file in java_file:
                print(file)
                diffs = file.diff
                print(diffs)

if __name__ == '__main__':
    main()
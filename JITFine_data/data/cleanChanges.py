import json
import pandas as pd

from mongoengine import connect, DoesNotExist
from pycoshark.mongomodels import Commit, FileAction, File, Project, VCSSystem, Hunk, Issue, IssueSystem, Refactoring
from pycoshark.utils import create_mongodb_uri_string
from pathlib import Path
from pydriller import Git
from data.utils import java_filename_filter

PROJECT_URL = Path('~/JITFine/project_urls.csv')
use_mongodb = False
credentials = {'db_user': '',
               'db_password': '',
               'db_hostname': 'localhost',
               'db_port': 27017,
               'db_authentication_database': '',
               'db_ssl_enabled': False}

database_name = 'smartshark_1_3'


def main():
    use_mongodb = True
    if use_mongodb:
        uri = create_mongodb_uri_string(**credentials)
        connect(database_name, host=uri, alias='default')
        project2commits = dict()
        for idx, url in enumerate(project_url.values):
            # if idx != 7:
            #     continue
            url = url[0]
            print(idx, url)
            vcs = VCSSystem.objects(url=url.strip()).get()
            # print(vcs.id)
            commits = [c.revision_hash for c in Commit.objects(vcs_system_id=vcs.id).only('revision_hash')]
            project2commits[url] = commits

        for idx, url in enumerate(project_url.values):
            url = url[0]
            if 'wss4j' in url or 'santuario-java' in url:
                continue
            print(idx, url)
            # vcs = VCSSystem.objects(url=url.strip()).get()
            # if idx < 7:
            #     continue
            print(vcs.id)
            commits = project2commits[url]
            print('mongodb commits cnt: ', len(commits))
            # get clean commits
            project_name = url.split('/')[-1].split('.')[0]
            import os
            current_directory = os.getcwd()
            project_path = os.path.join(current_directory, 'repos', project_name)
            gr = Git(project_path)
            local_commits = list(gr.get_list_commits())
            print('local repo commits cnt: ', len(local_commits))
            # tmp = [c.hash for c in local_commits if
            #        any([java_filename_filter(file.new_path if file.new_path else file.old_path) for file in c.modified_files])]
            tmp = [c.hash for c in local_commits]
            # print('local repo commits having .java cnt: ', len(tmp))
            commits = [c for c in commits if c in tmp]
            print('mongodb commits in local repo cnt: ', len(commits))
            bic = proj2bic[project_name]
            clean_commits = list()

            for commit in commits:
                if commit not in bic and commit not in clean_commits:
                    commit_ins = gr.get_commit(commit)
                    if commit_ins.lines >= 10000 or commit_ins.files >= 100 \
                            or commit_ins.insertions == 0:
                        continue
                    # print(len(commit_ins.modified_files))
                    # for file in commit_ins.modified_files:
                    #     java_file = [java_filename_filter(file.new_path if file.new_path else file.old_path,
                    #                                       production_only=only_production_code)]
                    java_file = [java_filename_filter(file.new_path if
                                                      file.new_path else file.old_path,
                                                      production_only=only_production_code) for file in
                                 commit_ins.modified_files]
                    if not any(java_file):
                        continue
                    clean_commits.append(commit)
            project2clean[project_name] = clean_commits
            print('clean commits: ', len(clean_commits), 'buggy commits: ', len(bic))
            # print(len(clean_commits), len(bic), (len(clean_commits)+len(bic) == len(commits)), abs(len(clean_commits)+len(bic) - len(commits)))
            # break
        return


if __name__ == '__main__':
    only_production_code = False
    project_url = pd.read_csv(PROJECT_URL, index_col=0)
    print(only_production_code)
    if only_production_code:
        with open('./data/only_production_code/buggy_commits_only_production_code.json', 'r') as f:
            proj2bic = json.load(f)

    else:
        with open('./data/all_changes_data/buggy_commits.json', 'r') as f:
            proj2bic = json.load(f)
    project2clean = dict()
    main()
    if only_production_code:
        with open('./data/only_production_code/clean_commits_only_production_code.json', 'w') as f:
            json.dump(project2clean, f)
    else:
        with open('./data/all_changes_data/clean_commits.json', 'w') as f:
            json.dump(project2clean, f)

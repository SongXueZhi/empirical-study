import json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from matplotlib.dates import MONTHLY, WEEKLY, DateFormatter, rrulewrapper, RRuleLocator
from pandas.plotting import register_matplotlib_converters

from mongoengine import connect, DoesNotExist
from pycoshark.mongomodels import Commit, FileAction, File, Project, VCSSystem, Hunk, Issue, IssueSystem, Refactoring
from pycoshark.utils import create_mongodb_uri_string, java_filename_filter
from bson import json_util
from scipy import stats
from scipy import optimize
from itertools import chain

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

        completed = []
        # cache hunks locally to avoid timeouts
        # tmp_hunks = [h for h in Hunk.objects(lines_manual__exists=True).only('id', 'lines_manual', 'file_action_id')]
        tmp_hunks = [h for h in Hunk.objects(lines_manual__exists=True)]
        print(len(tmp_hunks))

        for h in tmp_hunks:
            if len(h.lines_manual) > 3:
                fa = FileAction.objects(id=h.file_action_id).get()
                file = File.objects(id=fa.file_id).get()
                old_file = None
                if 'old_file_id' in fa:
                    old_file = File.objects(id=fa.old_file_id).get()
                commit = Commit.objects(id=fa.commit_id).only('revision_hash', 'fixed_issue_ids', 'vcs_system_id').get()
                vcs = VCSSystem.objects(id=commit.vcs_system_id).get()
                project = Project.objects(id=vcs.project_id).get()
                external_id = None
                num_fixed_bugs = 0
                for issue in Issue.objects(id__in=commit.fixed_issue_ids):
                    if issue.issue_type_verified is not None and issue.issue_type_verified.lower() == 'bug':
                        num_fixed_bugs += 1
                        external_id = issue.external_id
                if num_fixed_bugs == 1:
                    completed.append({
                        'project': project.name,
                        'revision_hash': commit.revision_hash,
                        'lines_verified': h.lines_verified,
                        'file': file.path,
                        'mode': fa.mode,
                        'old_file': old_file.path if old_file else '',
                        'new_start': h.new_start,
                        'new_lines': h.new_lines,
                        'old_start': h.old_start,
                        'old_lines': h.old_lines,
                        'content': h.content,
                        'hunk_id': h.id,
                        'repository_url': vcs.url,
                        'lines_manual': h.lines_manual,
                    })
                else:
                    pass  # this is just in case we start labeling commits that link to multible bugs

        # store to disk
        with open('./hunk_labels.json', 'w') as file:
            file.write(json_util.dumps(completed))
    else:
        print("skipping (use_mongodb==False)")


if __name__ == '__main__':
    main()

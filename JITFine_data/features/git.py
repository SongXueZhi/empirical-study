import os
import subprocess
import json
from classifier.classifier import *  # Used for classifying each commit
from classifier.commitFile import *  # Used for representing a file
from data.utils import java_filename_filter
import time
import math
from pydriller import Git as pyGit, Repository
import re

"""
file: repository.py
authors: Ben Grawi <bjg1568@rit.edu>, Christoffer Rosen <cbr4830@rit.edu>
date: October 2013
description: Holds the repository git abstraction class
"""


class Git:
    """
    Git():
    pre-conditions: git is in the current PATH
                    self.path is set in a parent class
    description: a very basic abstraction for using git in python.
    """
    # Two backslashes to allow one backslash to be passed in the command.
    # This is given as a command line option to git for formatting output.

    # A commit mesasge in git is done such that first line is treated as the subject,
    # and the rest is treated as the message. We combine them under field commit_message

    # We want the log in ascending order, so we call --reverse
    # Numstat is used to get statistics for each commit
    LOG_FORMAT = '--pretty=format:\" CAS_READER_STARTPRETTY\
    \\"parent_hashes\\"CAS_READER_PROP_DELIMITER: \\"%P\\",CAS_READER_PROP_DELIMITER2\
    \\"commit_hash\\"CAS_READER_PROP_DELIMITER: \\"%H\\",CAS_READER_PROP_DELIMITER2\
    \\"author_name\\"CAS_READER_PROP_DELIMITER: \\"%an\\",CAS_READER_PROP_DELIMITER2\
    \\"author_email\\"CAS_READER_PROP_DELIMITER: \\"%ae\\",CAS_READER_PROP_DELIMITER2\
    \\"author_date\\"CAS_READER_PROP_DELIMITER: \\"%ad\\",CAS_READER_PROP_DELIMITER2\
    \\"author_date_unix_timestamp\\"CAS_READER_PROP_DELIMITER: \\"%at\\",CAS_READER_PROP_DELIMITER2\
    \\"commit_message\\"CAS_READER_PROP_DELIMITER: \\"%s%b\\"\
    CAS_READER_STOPPRETTY \" --numstat --reverse --all'

    # git clone command w/o downloading src code
    CLONE_CMD = 'git clone {!s} {!s}'  # !s（apply str()）和!r（apply repr()）可用于在格式化之前转换值。
    PULL_CMD = 'git pull'  # git pull command
    RESET_CMD = 'git reset --hard FETCH_HEAD'
    CLEAN_CMD = 'git clean -df'  # f for force clean, d for untracked directories

    # directory in which to store repositories
    REPO_DIRECTORY = "repos/"

    def __init__(self, logging=None):
        """
        constructor
        """
        self.logger = logging

    def _getCommitStatsProperties(self, stats, commitFiles, devExperience, author, unixTimeStamp,
                                  only_production_code=False):
        """
        getCommitStatsProperties
        Helper method for log. Caclulates statistics for each change/commit and
        returns them as a comma seperated string. Log will add these to the commit object
        properties

        @param stats            These are the stats given by --numstat as an array
        @param commitFiles      These are all tracked commit files
        @param devExperience    These are all tracked developer experiences
        @param author           The author of the commit
        @param unixTimeStamp    Time of the commit
        """
        statProperties = ""

        # Data structures to keep track of info needed for stats
        subsystemsSeen = []  # List of system names seen
        directoriesSeen = []  # List of directory names seen
        # List of modified loc in each file seen
        locModifiedPerFile = []
        # List of all unique authors seen for each file
        authors = []
        # List of the ages for each file in a commit
        fileAges = []

        # Stats variables
        la = 0  # lines added
        ld = 0  # lines deleted
        nf = 0  # Number of modified files
        ns = 0  # Number of modified subsystems
        nd = 0  # number of modified directories
        # entropy: distriubtion of modified code across each file
        entropy = 0
        # lines of code in each file (sum) before the commit
        lt = 0
        # the number of developers that modifed the files in a commit
        ndev = 0
        # the average time interval between the last and current change
        age = 0
        # number of changes made by author previously
        exp = 0
        # experience weighted by age of files ( 1 / (n + 1))
        rexp = 0
        # changes made previous by author in same subsystem
        sexp = 0
        totalLOCModified = 0  # Total modified LOC across all files
        nuc = 0  # number of unique changes to the files
        filesSeen = ""  # files seen in change/commit
        for stat in stats:

            if (stat == ' ' or stat == ''):
                continue
            # 1\t1\t.editorconfig
            # 29\t0\t.eslintrc.js
            fileStat = stat.split("\\t")

            # Check that we are only looking at file stat (i.e., remove extra newlines)
            if (len(fileStat) < 2):
                continue

            # catch the git "-" line changes
            try:
                fileLa = int(fileStat[0])
                fileLd = int(fileStat[1])
            except:
                fileLa = 0
                fileLd = 0

            # Remove oddities in filename so we can process it

            fileName = (fileStat[2].replace(
                "'", '').replace('"', '').replace("\\", ""))
            # src/test/java/org/apache/commons/codec/digest/{MessageDigestAlgorithmTest.java => MessageDigestAlgorithmsTest.java}
            # --numstat对于rename会返回这样的名字要处理

            if '=>' in fileName:
                segments = re.split(r'{(.*)}', fileName)
                fileName = ''
                for sub in segments:
                    if '=>' in sub:
                        fileName += sub.split('=> ')[-1]
                    else:
                        fileName += sub

            if not java_filename_filter(fileName, production_only=only_production_code):
                continue

            totalModified = fileLa + fileLd

            # have we seen this file already?
            if (fileName in commitFiles):
                prevFileChanged = commitFiles[fileName]
                prevLOC = getattr(prevFileChanged, 'loc')
                prevAuthors = getattr(prevFileChanged, 'authors')
                prevChanged = getattr(prevFileChanged, 'lastchanged')
                file_nuc = getattr(prevFileChanged, 'nuc')
                nuc += file_nuc
                lt += prevLOC

                for prevAuthor in prevAuthors:
                    if prevAuthor not in authors:
                        authors.append(prevAuthor)

                # Convert age to days instead of seconds
                age += ((int(unixTimeStamp) - int(prevChanged)) / 86400) * 1.0
                fileAges.append(prevChanged)

                # Update the file info

                file_nuc += 1  # file was modified in this commit
                setattr(prevFileChanged, 'loc', prevLOC + fileLa - fileLd)
                setattr(prevFileChanged, 'authors', authors)
                setattr(prevFileChanged, 'lastchanged', unixTimeStamp)
                setattr(prevFileChanged, 'nuc', file_nuc)

            else:

                # new file we haven't seen b4, add it to file commit files dict
                if (author not in authors):
                    authors.append(author)

                if (unixTimeStamp not in fileAges):
                    fileAges.append(unixTimeStamp)

                fileObject = CommitFile(
                    fileName, fileLa - fileLd, authors, unixTimeStamp)
                commitFiles[fileName] = fileObject

            # end of stats loop

            locModifiedPerFile.append(totalModified)  # Required for entropy
            totalLOCModified += totalModified
            fileDirs = fileName.split("/")

            if (len(fileDirs) == 1):
                subsystem = "root"
                directory = "root"
            else:
                subsystem = fileDirs[0]
                directory = "/".join(fileDirs[0:-1])

            if (subsystem not in subsystemsSeen):
                subsystemsSeen.append(subsystem)

            if (directory not in directoriesSeen):
                directoriesSeen.append(directory)

            # Update file-level metrics
            la += fileLa
            ld += fileLd
            nf += 1
            filesSeen += fileName + ",CAS_DELIMITER,"

        # End stats loop

        if (nf < 1):
            return ""
        # experience

        if (author in devExperience):
            experiences = devExperience[author]
            for subsystem in subsystemsSeen:
                if (subsystem in experiences['subs']):
                    sexp += experiences['subs'][subsystem]
                    experiences['subs'][subsystem] += 1
                else:
                    experiences['subs'][subsystem] = 1
        else:
            # devExperience[author] = {subsystem: 1}
            devExperience[author] = dict()
            devExperience[author]['changes'] = list()
            devExperience[author]['subs'] = {subsystem: 1}

        exp = len(devExperience[author]['changes'])
        if exp > 0:
            for time_stamp in devExperience[author]['changes']:
                try:
                    denominator = ((int(unixTimeStamp) - int(time_stamp)) / 86400 / 365) * 1.0
                    rexp += (1 / (denominator + 1))
                except:
                    rexp += 0

        # Update commit-level metrics
        ns = len(subsystemsSeen)
        nd = len(directoriesSeen)
        ndev = len(authors)
        lt = lt / nf
        age = age / nf
        exp = exp / 1.0
        rexp = rexp / 1.0
        sexp = sexp / ns

        # Update entropy
        for fileLocMod in locModifiedPerFile:
            if (fileLocMod != 0):
                avg = fileLocMod / totalLOCModified
                entropy -= (avg * math.log(avg, 2))

        devExperience[author]['changes'].append(unixTimeStamp)
        # Add stat properties to the commit object
        statProperties += ',"la":"' + str(la) + '\"'
        statProperties += ',"ld":"' + str(ld) + '\"'
        statProperties += ',"fileschanged":"' + filesSeen[0:-1] + '\"'
        statProperties += ',"nf":"' + str(nf) + '\"'
        statProperties += ',"ns":"' + str(ns) + '\"'
        statProperties += ',"nd":"' + str(nd) + '\"'
        statProperties += ',"entropy":"' + str(entropy) + '\"'
        statProperties += ',"ndev":"' + str(ndev) + '\"'
        statProperties += ',"lt":"' + str(lt) + '\"'
        statProperties += ',"nuc":"' + str(nuc) + '\"'
        statProperties += ',"age":"' + str(age) + '\"'
        statProperties += ',"exp":"' + str(exp) + '\"'
        statProperties += ',"rexp":"' + str(rexp) + '\"'
        statProperties += ',"sexp":"' + str(sexp) + '\"'

        return statProperties

    # End stats

    def log(self, project, only_production_code=False):
        """
        log(): Repository, Boolean -> Dictionary
        arguments: repo Repository: the repository to clone
                   firstSync Boolean: whether to sync all commits or after the
            ingestion date
        description: a very basic abstraction for using git in python.
        """
        # repo_dir = os.chdir(os.path.dirname(__file__) +
        #                     self.REPO_DIRECTORY + repo.repository_id)
        repo_dir = self.REPO_DIRECTORY + project
        self.logger.info('Getting/parsing git commits: ' + str(project))

        import os

        # 获取当前工作目录
        current_directory = os.getcwd()
       
        repo_dir = os.path.join(current_directory, repo_dir)
        print("当前工作目录是:", repo_dir)

        cmd = 'git log '
        # 创建子进程获得 log
        log = str(subprocess.check_output(
            cmd + self.LOG_FORMAT, shell=True, cwd=repo_dir))
        # print('fe96b3bb16be25bf936daac1d004e579f1ca770a' in log)
        # return
        log = log[2:-1]  # Remove head/end clutter

        # List of json objects
        json_list = []

        # Make sure there are commits to parse
        if len(log) == 0:
            return []

        commitFiles = dict()  # keep track of ALL file changes
        devExperience = dict()  # Keep track of ALL developer experience
        # classifier for classifying commits (i.e., corrective, feature addition, etc)
        classifier = Classifier()
        allCommit = []
        commitList = log.split("CAS_READER_STARTPRETTY")
        for commit in commitList:

            author = ""  # author of commit
            unixTimeStamp = 0  # timestamp of commit
            fix = False  # whether or not the change is a defect fix
            # classification of the commit (i.e., corrective, feature addition, etc)
            classification = None
            isMerge = False  # whether or not the change is a merge

            # Remove invalid json escape characters
            commit = commit.replace('\\x', '\\u00')

            # split the commit info and its stats
            splitCommitStat = commit.split("CAS_READER_STOPPRETTY")

            # The first split will contain an empty list
            if (len(splitCommitStat) < 2):
                continue

            prettyCommit = splitCommitStat[0]
            statCommit = splitCommitStat[1]

            commitObject = ""

            # Start with the commit info (i.e., commit hash, author, date, subject, etc)
            prettyInfo = prettyCommit.split(',CAS_READER_PROP_DELIMITER2    "')
            for propValue in prettyInfo:
                props = propValue.split('"CAS_READER_PROP_DELIMITER: "')
                propStr = ''
                for prop in props:
                    # avoid escapes & newlines for JSON formatting
                    prop = prop.replace('\\', '').replace("\\n", '')
                    propStr = propStr + '"' + prop.replace('"', '') + '":'

                values = propStr[0:-1].split(":")

                if (values[0] == '"    parent_hashes"'):
                    # Check to see if this is a merge change. Fix for Issue #26.
                    # Detects merges by counting the # of parent commits

                    parents = values[1].split(' ')
                    if len(parents) == 2:
                        isMerge = True
                if (values[0] == '"commit_hash"'):
                    commitHash = values[1].replace('"', '')
                    if commitHash == 'f0299220ba7dc33b1865068db0c184147283a9e4':
                        print('abc')
                    allCommit.append(commitHash)
                if (values[0] == '"author_name"'):
                    author = values[1].replace('"', '')

                if (values[0] == '"author_date_unix_timestamp"'):
                    unixTimeStamp = values[1].replace('"', '')

                # Classify the commit
                if (values[0] == '"commit_message"'):

                    if (isMerge):
                        classification = "Merge"
                    else:
                        classification = classifier.categorize(
                            values[1].lower())

                    # If it is a corrective commit, we induce it fixes a bug somewhere in the system
                    if classification == "Corrective":
                        fix = True

                commitObject += "," + propStr[0:-1]
                # End property loop
            # End pretty info loop

            # Get the stat properties
            stats = statCommit.split("\\n")

            commitObject += self._getCommitStatsProperties(stats, commitFiles, devExperience, author,
                                                           unixTimeStamp, only_production_code)
            # Update the classification of the commit
            commitObject += ',"classification":"' + str(classification) + '\"'

            # Update whether commit was a fix or not
            commitObject += ',"fix":"' + str(fix) + '\"'

            # Remove first comma and extra space
            commitObject = commitObject[1:].replace('    ', '')
            # Add commit object to json_list

            json_list.append(json.loads('{' + commitObject + '}'))
        # End commit loop

        # print(repo_dir,os.path.dirname(__file__)+self.REPO_DIRECTORY+repo.repository_id)
        # print(os.path.dirname(__file__),
        #                     self.REPO_DIRECTORY ,repo.repository_id)
        self.logger.info('Done getting/parsing git commits.')
        print(len(json_list))
        return json_list

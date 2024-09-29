import pygit2


def getDiffFromRepo(repoPath, commit_hash):
    repo = pygit2.Repository(repoPath)
    if commit_hash[1] == '_':
        commit_hash = commit_hash[2:]
    commit = repo.revparse_single(commit_hash)
    # 获取提交的第一个父提交
    parent_commit = commit.parents[0]
    # 获取提交的 diff 对象
    diff = commit.tree.diff_to_tree(parent_commit.tree)
    # 存储每个文件的新增和删除行
    file_changes = {}
    # 遍历 diff，逐个文件获取修改内容
    for patch in diff:
        delta = patch.delta
        # 根据文件状态确定文件路径
        if delta.status == pygit2.GIT_DELTA_DELETED:
            file_path = delta.old_file.path
        else:
            file_path = delta.new_file.path

        added_lines = []
        removed_lines = []

        # 遍历每个 hunk（更改的块）
        for hunk in patch.hunks:
            # 遍历每个 hunk 中的行
            for line in hunk.lines:
                # 判断是否是新增的行
                if line.origin == '+' and line.content.strip():
                    added_lines.append(line.content.strip())
                # 判断是否是删除的行
                elif line.origin == '-' and line.content.strip():
                    removed_lines.append(line.content.strip())

        # 将文件的新增和删除行保存到字典中
        file_changes[file_path] = {
            'added_code': added_lines,
            'removed_code': removed_lines
        }
    return file_changes


if __name__ == '__main__':
    repoPath = '/Users/sxz/Documents/coding/project/empirical-study/JITFine_data/repos/cron-utils'
    commit_hash = 'ff67527e69868a2c2b05ab8a1ddcca8d8f896e44'
    file_changes = getDiffFromRepo(repoPath, commit_hash)
    print(file_changes)

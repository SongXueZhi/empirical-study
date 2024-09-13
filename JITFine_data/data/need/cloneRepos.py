from joblib import Parallel, delayed
# from config import PROJECT_URL, CLONE_PATH, CLONE_LOG
import pandas as pd
import subprocess
from pathlib import Path
import platform

import os
current_directory = os.getcwd()
PROJECT_URL = os.path.join(current_directory, 'project_urls.csv')

CLONE_PATH = os.path.join(current_directory, 'repos')

def clone_repo(url):
    target_path = f"{CLONE_PATH}/{url.split('/')[-1].split('.')[0]}"
    cmd = f"git clone {url} {target_path}"
    target_path = Path(target_path)
    try:
        if not target_path.exists():
            subprocess.call(cmd, shell=True)
    except Exception as e:
        print(e)


def main():
    project_url = pd.read_csv(PROJECT_URL)
    print(project_url.shape)
    if not CLONE_PATH.exists():
        CLONE_PATH.mkdir(parents=True, exist_ok=True)
    Parallel(n_jobs=4)(delayed(clone_repo)(item.values.tolist()[1])
                       for _, item in project_url.iterrows())


if __name__ == '__main__':
    system = platform.system()
    # print(clone_path, system)
    main()

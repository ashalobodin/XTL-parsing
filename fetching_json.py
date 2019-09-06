# You need to create a ../maps directory
import json
import os
import threading
import concurrent.futures
import time
import sys

from requests import Session as RequestSession, HTTPError

thread_local = threading.local()


def get_session():
    if not getattr(thread_local, "session", None):
        thread_local.session = RequestSession()
    return thread_local.session


def verify_resp_json(path, key=None):
    session = RequestSession() if key else get_session()
    resp = session.get(path)
    resp.raise_for_status()
    return resp.json() if not key else resp.json()[key]


def with_args(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper


def fetch_json(start=0):
    list_repos = 'https://xd.spsc.io/xd/list'
    list_files = 'https://xd.spsc.io/xd/list/{repo}/master'
    jsons = 'https://xd.spsc.io/xd/json/{repo}/master/{file}'

    @with_args
    def _fetch_file_content(filename):
        try:
            file_content_json = verify_resp_json(jsons.format(repo=repo_name, file=filename))
            fn = filename.replace('/', '_') + '.json'
            with open(os.path.join(path, fn), 'w') as f:
                json.dump(file_content_json, f)
        except HTTPError as exc:
            print(exc.message)

    repos = sorted(filter(lambda x: x[-4:] == '.web', verify_resp_json(list_repos, 'repos')))
    print('Found {} repos.'.format(len(repos)))

    i = 0
    for repo_name in repos[start:]:
        try:
            files = filter(lambda fn: fn[-4:] == '.xtl', verify_resp_json(list_files.format(repo=repo_name), 'files'))
        except HTTPError as exc:
            i += 1
            print(exc.message)
            continue

        t1 = time.time()
        print('{}. Repo name is {}: {} files'.format(start + i, repo_name, len(files)))

        path = os.path.join(os.path.abspath('.'), '../maps2', repo_name)

        if not os.path.exists(path):
            os.makedirs(path)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(_fetch_file_content, files))

            print('\tIt took {}'.format(time.time() - t1))
        else:
            print('Path exists. Skipping.')

        i += 1


if __name__ == "__main__":
    try:
        start = int(sys.argv[1] if len(sys.argv) > 1 else 0)
    except:
        start = 0

    fetch_json(start)

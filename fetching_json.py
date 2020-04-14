# You need to create a ../maps directory
import json
import os
import threading
import concurrent.futures
import time
import sys

from requests import Session as RequestSession, HTTPError

from mandatory_fields import write_file

thread_local = threading.local()
FILENAME = 'download.log'


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
    write_file('Starting with {}.\n'.format(start), filename=FILENAME)
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
            del file_content_json
        except HTTPError as exc:
            write_file(exc.message+'\n', filename=FILENAME)

    repos = sorted(filter(lambda x: x[-4:] == '.web', verify_resp_json(list_repos, 'repos')))
    write_file('Found {} repos.\n'.format(len(repos)), filename=FILENAME)

    i = 0
    for repo_name in repos[start:]:
        try:
            files = filter(lambda fn: fn[-4:] == '.xtl', verify_resp_json(list_files.format(repo=repo_name), 'files'))
        except HTTPError as exc:
            i += 1
            write_file(exc.message+'\n', filename=FILENAME)
            continue

        t1 = time.time()
        write_file('{}. Repo name is {}: {} files.\n'.format(start + i, repo_name, len(files)), filename=FILENAME)

        path = os.path.join(os.path.abspath('.'), '../maps', repo_name)

        if not os.path.exists(path):
            os.makedirs(path)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(_fetch_file_content, files))

            write_file('\tIt took {}.\n'.format(time.time() - t1), filename=FILENAME)
        else:
            write_file('Path exists. Skipping.\n', filename=FILENAME)

        i += 1


if __name__ == "__main__":
    try:
        start = int(sys.argv[1] if len(sys.argv) > 1 else 0)
    except:
        start = 0

    fetch_json(start)

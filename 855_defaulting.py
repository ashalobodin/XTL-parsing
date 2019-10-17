import json
import os
import sys
import re

# Based on code, written by Laszlo Szathmary, alias Jabba Laci, 2017, jabba.laci@gmail.com

BASE_RESULT_DIR = 'results'


class DefaultingFound(Exception):
    pass


defaulting_855_pattern = r'[D|d]efaulting[\w\s]*[A|a]cknowledgment'

files = sorted([os.path.join(dp, f) for dp, dn, filenames in os.walk('../maps3')
                for f in filenames if os.path.splitext(f)[1] == '.json'])


def traverse(path, obj):
    cnt = -1
    if isinstance(obj, dict):
        d = obj
        if 'atts' in obj.keys():
            if obj['atts'].get('name') and re.search(defaulting_855_pattern, obj['atts']['name']):
                raise DefaultingFound

        for k, v in d.items():
            if isinstance(v, (dict, list)):
                traverse(path + '.' + k, v)

    if isinstance(obj, list):
        li = obj
        for e in li:
            cnt += 1
            if isinstance(e, (dict, list)):
                traverse("{path}[{cnt}]".format(path=path, cnt=cnt), e)


def write_file(lines, mode='a', filename='855_no_defaulting.txt'):
    path = os.path.join(BASE_RESULT_DIR, filename)
    with open(path, mode) as f:
        try:
            f.writelines(lines)
        except Exception as e:
            print lines
            raise


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else len(files)
    write_file('', 'w')
    print('There are {} files'.format(count))
    no_defaulting = []
    for i, item in enumerate(files[:count]):
        try:
            with open(item) as f:
                json_obj = json.load(f)
        except ValueError as e:
            write_file('Error loading form {}: {}\n'.format(item.replace('../maps3/', ''), e.message))
            continue

        try:
            map_attibutes = json_obj['children'][0]['atts']
            if map_attibutes['type'] != '855':
                del json_obj
                continue
        except KeyError as e:
            continue
        try:
            traverse('root', json_obj)
            no_defaulting.append(item.replace('../maps3/', '') + ', {}.{}\n'.format(
                json_obj['children'][0]['atts']['javaPackageName'], json_obj['children'][0]['atts']['javaName']))
        except DefaultingFound:
            pass

        if i % 100 == 0:
            print 'Parced {} files. Length of no_defaulting is {}'.format(i, len(no_defaulting))
        del json_obj

    write_file(no_defaulting)
    print 'Done'

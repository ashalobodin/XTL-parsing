import json
import os
import re
import sys

# Based on code, written by Laszlo Szathmary, alias Jabba Laci, 2017, jabba.laci@gmail.com

BASE_RESULT_DIR = 'results'


files = sorted([os.path.join(dp, f) for dp, dn, filenames in os.walk('../maps2')
                for f in filenames if os.path.splitext(f)[1] == '.json'])


def traverse(path, obj, entity_path, data=[]):
    cnt = -1
    if isinstance(obj, dict):
        d = obj
        if 'atts' in obj.keys():
            if obj['atts'].get('mandatory'):
                data.append({
                    'name': entity_path + '.' + obj['atts'].get('javaName', 'EMPTY_javaName'),
                    'mandatory': obj['atts'].get('mandatory'),
                    'source': obj['atts'].get('source', '')
                })

        for k, v in d.items():
            if isinstance(v, dict):
                if v.get('javaName'):
                    entity_path += '.' + v['javaName'] if entity_path else v['javaName']
                traverse(path + '.' + k, v, entity_path, data)
            elif isinstance(v, list):
                traverse(path + '.' + k, v, entity_path, data)
            else:
                # skipping other keys like 'text', 'java' etc
                pass

    if isinstance(obj, list):
        li = obj
        for e in li:
            cnt += 1
            if isinstance(e, dict):
                traverse("{path}[{cnt}]".format(path=path, cnt=cnt), e, entity_path, data)
            elif isinstance(e, list):
                traverse("{path}[{cnt}]".format(path=path, cnt=cnt), e, entity_path, data)
            else:
                print("{path}[{cnt}] => {e}".format(path=path, cnt=cnt, e=e))

    return data


def write_file(lines, mode='a', filename='fulfil_6244.txt'):
    path = os.path.join(BASE_RESULT_DIR, filename)
    with open(path, mode) as f:
        f.writelines(lines)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else len(files)
    write_file('', 'w')
    for item in files[:count]:
        try:
            with open(item) as f:
                json_obj = json.load(f)
        except ValueError as e:
            write_file('Error loading form {}: {}'.format(item, e.message))
            continue

        try:
            map_attibutes = json_obj['children'][0]['atts']
        except KeyError as e:
            continue

        data = traverse('root', json_obj, '', [])
        write_file(['{}/{}.jar,{},{},{}\n'.format(map_attibutes['javaPackageName'],
                                                  map_attibutes['javaName'],
                                                  obj['name'],
                                                  obj['mandatory'],
                                                  obj['source']) for obj in data])
        del json_obj, data,

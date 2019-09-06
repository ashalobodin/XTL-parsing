import json
import os
import re
import sys

# Based on code, written by Laszlo Szathmary, alias Jabba Laci, 2017, jabba.laci@gmail.com

java_patterns = {
#    'src_eq_null': re.compile(r'if\s*\(\s*\w+\(?\)?\s*[!|=]=\s*null\s*[a-zA-Z\(\)|\s.]*\)\s*\{?'),
    'src_eq_null': re.compile(r'if\s*\(\s*.+\(?\)?\s*[!|=]=\s*null'),
#    'src_eq_null': re.compile(r'if\s*\(\s*\w+\(?\)?\s*==\s*null\s*[a-zA-Z\(\)|\s.]*\)\s*\{?\s*return;'),
#    'src_ne_null': re.compile(r'if\s*\(\s*\w+\(?\)?\s*!=\s*null\s*[a-zA-Z\(\)|\s.]*\)\s*\{?'),
    'get_source': re.compile(r'[getS|_s]ource\(\)')
}

files = sorted([os.path.join(dp, f) for dp, dn, filenames in os.walk('../maps2')
                for f in filenames if os.path.splitext(f)[1] == '.json'])


def traverse(path, obj, data=[]):
    cnt = -1
    if isinstance(obj, dict):
        d = obj

        for k, v in d.items():
            if isinstance(v, dict):
                traverse(path + "." + k, v, data)
            elif isinstance(v, list):
                traverse(path + "." + k, v, data)
            else:

                if k == 'text' and d.get('name') == 'java':
                    get_source = java_patterns['get_source'].findall(v)
                    src_eq_null = java_patterns['src_eq_null'].findall(v)
                    #src_ne_null = java_patterns['src_ne_null'].findall(v)
                    if get_source and not (src_eq_null):# or src_ne_null):
                        data.append(v[:200])

    if isinstance(obj, list):
        li = obj
        for e in li:
            cnt += 1
            if isinstance(e, dict):
                traverse("{path}[{cnt}]".format(path=path, cnt=cnt), e, data)
            elif isinstance(e, list):
                traverse("{path}[{cnt}]".format(path=path, cnt=cnt), e, data)
            else:
                print("{path}[{cnt}] => {e}".format(path=path, cnt=cnt, e=e))
    return data


def write_file(lines, mode='a', filename='raw_data.txt'):
    with open(filename, mode) as f:
        f.writelines(lines)


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else len(files)
    # write_file(' Parsing {} of {} forms. '.format(count, len(files)).center(100, '=') + '\n'
    #            '====\tEach line consists of javaPackageName.javaName: number_of_findings:\n'
    #            '====\tand a list of java code which doesn\'t pass validation (200 symbols).\n' +
    #            '='*100 + '\n', mode='w')
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

            if map_attibutes['type'] == '860' or not map_attibutes.get('source'):
                continue

        except KeyError as e:
            # write_file('==== KeyError \'{}\' for {} ====\n'.format(e.message, item))
            continue

        data = traverse('root', json_obj, [])
        if data:
            write_file('{}:{}:{}:{}\n'.format(map_attibutes['javaPackageName'], map_attibutes['javaName'], len(data), data))
        del json_obj
    # write_file('====================================================================================================\n')

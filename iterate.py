import time
import json
import os
import re
import sys
import pandas as pd

# Based on code, written by Laszlo Szathmary, alias Jabba Laci, 2017, jabba.laci@gmail.com

java_patterns = {
    'check_mandatory': re.compile(r'checkMandatory\(\w+, (\w+)\);'),
    'optional_group_mandatory_elements': re.compile(r'[_?root\(?\)?.]?[o|O]ptionalGroupMandatoryElements\(\w+,\s?\\?\"?[\w,| ]*\\?\"?,\s?\\?\"?([\w, ]+)\\?\"?\);'),
    'condition_requires_one': re.compile(r'[_?root\(?\)?.]?[c|C]onditionRequiresOne\(\w+,\s?\\?\"?[\w,| ]*\\?\"?,\s?\\?\"?([\w, ]+)\\?\"?\);'),
    'set_property': re.compile(r'[\\t\s]+(\w+).setProperty\(\\?\"mandatory\\?\"?,\s?\\?\"?[Ytrue]+\\?\"?\);'),
    'DGEProperties_mandatory': re.compile(r'DGEProperties\.mandatory\.set\(\s?\\?\"?([_\(\)\.\w]+)\\?\"?,\s?\\?\"?[Ytrue]+\\?\"?\);'),
}

files = [os.path.join(dp, f) for dp, dn, filenames in os.walk('../maps') for f in filenames if
             os.path.splitext(f)[1] == '.json']

conditionals = dict()


def _split(data):
    ret = []
    for item in data:
        ret.extend(item.split(','))
    return ret


def traverse(path, obj, data={}):
    cnt = -1
    if isinstance(obj, dict):
        d = obj
        if 'atts' in obj.keys():
            if not obj['atts'].get('mandatory') and obj['atts'].get('condition') and obj['atts'].get('conditionElements'):
                data['web_xd'].extend(obj['atts'].get('conditionElements').split(','))

        for k, v in d.items():
            if isinstance(v, dict):
                traverse(path + "." + k, v, data)
            elif isinstance(v, list):
                traverse(path + "." + k, v, data)
            else:
                # print('{}.{}  --> {}'.format(path, k, v.replace('\n', ' ')))

                if k == 'text':
                    pass
                    # for key in java_patterns.keys():
                    #     _check = java_patterns[key].findall(v)
                    #     if key in ('check_mandatory', 'optional_group_mandatory_elements', 'condition_requires_one'):
                    #         _check = _split(_check)
                    #     if _check:
                    #         data[key].extend(_check)

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


def iterate(count):
    processing_time = []
    for item in files[:count]:
        t = _process_item(item)
        if t:
            processing_time.append(t)

    lp = len(processing_time)
    if lp % 1000 == 0:
        print('Processed {} files. Average processing time {}'.format(lp, sum(processing_time) / lp))


def _process_item(item):
    try:
        with open(item) as f:
            json_obj = json.load(f)
    except ValueError as e:
        print('Error loading form {}: {}'.format(item, e.message))
        return None

    t1 = time.time()

    data = {key: [] for key in java_patterns.keys()}
    data['web_xd'] = []

    data = traverse('root', json_obj, data)
    # print data
    conditionals.update({item: {'java_'+key: len(data[key]) for key in java_patterns.keys()}})
    conditionals[item].update({'web_xd': len(data['web_xd'])})

    del json_obj

    return time.time() - t1


if __name__ == "__main__":
    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else len(files)
        print('===============================================================')
        print('Parsing {} of {} forms'.format(count, len(files)))

        iterate(count)

        stats = 'stats_for_{}.json'.format(count)

    except ValueError:
        count = 1
        item = sys.argv[1]
        _process_item(item)

        stats = 'stats_for_{}.json'.format(item.replace('..', '').replace('/', '_s'))

    with open(stats, 'w') as f:
        json.dump(conditionals, f)

    df = pd.DataFrame(pd.read_json(stats)).T

    # set True if any method is used
    df['java'] = (df['java_check_mandatory'] != 0) | (df['java_optional_group_mandatory_elements'] != 0) | (
                df['java_condition_requires_one'] != 0) | (df['java_set_property'] != 0) | (
                             df['java_DGEProperties_mandatory'] != 0)

    unique_forms_count = df['java'].sum()

    print('\tFound {} unique forms with conditional fields logic in java - {}%'.format(
        unique_forms_count, round(unique_forms_count*100./count, 2)
    ))
    for method in java_patterns.keys():
        cnt = (df['java_' + method] != 0).sum()
        print('\t\tFound {} forms with conditional fields logic with {} - {}%'.format(
            cnt, method, round(cnt*100./count, 2)))

    cnt_web_xd = (df['web_xd'] != 0).sum()
    print('\tFound {} forms with conditional fields logic in web_xd - {}%'.format(
        cnt_web_xd, round(cnt_web_xd*100./count, 2)))

    print(df.describe(percentiles=[.9, .95, .99]))

    print('===============================================================')

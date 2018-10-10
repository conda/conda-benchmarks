import os
import json
import glob

# test_name = 'time_solve_r_essentials_r_base_conda_forge'
test_name = 'time_solve_anaconda_44'

for f in glob.glob("*.json"):
    with open(f) as fd:
        d = json.load(fd)
    if f != 'machine.json' and d:
        # timeval = ((d.get('results', {}) or {}).get(test_name, {}) or {}).get('result', [0])[0]
        # if timeval < 1.0 and f != "machine.json":
        #     print("remove {}".format(f))
        #     os.remove(f)
        if 'params' in d:
            if 'conda-env' not in d['params']:
                d['params']['conda-env'] = ""
                d['requirements']['conda-env'] = ""
            elif d['params']['conda-env'] == []:
                d['params']['conda-env'] = ""
                d['requirements']['conda-env'] = ""
        else:
            d['params'] = {'conda-env': ""}
            d['requirements']['conda-env'] = ""
        if "chardet-mock" in d['env_name']:
            d['env_name'] = d['env_name'].replace("chardet-mock", 'chardet-conda-env-mock')
        f = f.replace("chardet-mock", 'chardet-conda-env-mock')
        with open(f, 'w') as fd:
            json.dump(d, fd, indent=2)
    else:
        print("file {} appears corrupt".format(f))

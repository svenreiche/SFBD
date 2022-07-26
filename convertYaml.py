import yaml
import json
import os

def applyMacro(pvs_in,macros):    
    pvs = []
    for macro in macros:
        for key in macro:
            tag='$('+key+')'
            for pv in pvs_in:
                if tag in pv:
                    pvs.append(pv.replace(tag,macro[key]))
    for pv in pvs_in:   # copy the ones without macro
        if not '$(' in pv:
            pvs.append(pv)
    return pvs
            
    
def convert(filename):
    pvs = []
    path = os.path.dirname(filename)
    with open(filename) as f:
        try:
            content = yaml.load(f, Loader=yaml.SafeLoader)
            if 'include' in content.keys():
                if len(content['include']) > 0:
                    for cont in content['include']:
                        retpv = convert(path+'/'+cont['name'])
                        if 'macros' in cont.keys():
                            retpv = applyMacro(retpv,cont['macros'])
                        pvs =  pvs + retpv
            if 'pvs' in content.keys():
                if 'list' in content['pvs']:
                    for pv in content['pvs']['list']:
                        pvs.append(pv['name'])
                return pvs
            return None

        except yaml.YAMLError as e:
            print(e)
            return None
        return None

if __name__ == '__main__':
    pvs = convert('/sf/data/applications/snapshot/req/op/SF_settings.yaml')
    if pvs is None:
        print('No valid channels')
    else:
        newpath ='/sf/data/applications/BD-Snap/config/SF_settings_BD.json'
        pvjson={}
        for pv in pvs:
            spl = pv.split(':')
            if not spl[0] in pvjson.keys():
                pvjson[spl[0]]=[]
            pvjson[spl[0]].append(spl[1])
        with open(newpath,'w') as out:
            json.dump(pvjson,out,indent=2,sort_keys=True)
        print(len(pvs),'Channels found')



 

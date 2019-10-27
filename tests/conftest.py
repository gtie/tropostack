"""
Common test functionality/settings
"""
import json

def stack2dict(stack_obj):
    """
    Render the stack (to JSON and then) to a dictionary.
    """
    json_output = stack_obj.compile().to_json()
    return json.loads(json_output)


def key_by_rsc_type(rsc_dict):                  
    """                                     
    Reverses `rsc_dict` from ``{<title>:<resource_data>}`` form to the more
    convenient for testing {<resource_type>: [<resource_data>,...]}        
    """                                                   
    result = {}                                             
    for title, item in rsc_dict.items():                                      
        r_type = item.get('Type')                 
        result.setdefault(r_type, []).append(item)                       
    return result   



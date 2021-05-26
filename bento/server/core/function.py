"""
Create and retrieve Bento functions
"""

import json
import os

from .config import opts

def get_function(token):
    filename= f'{opts.functions_dir}/{token}.json'
    if os.path.exists(filename):
        with open(filename) as filein:
            function= json.load(filein)
        return function
    else:
        return None


def create_function(token, name, code):
    function= {'name': name, 'code': code} 
    filename= f'{opts.functions_dir}/{token}.json'
    with open(filename, 'w') as outfile:
        json.dump(function, outfile)

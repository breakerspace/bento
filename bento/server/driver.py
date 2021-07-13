"""
Executed in an execution broker spawned by server
"""

import struct
import json
import base64
import sys

import core.bentoapi as bentoapi


def _write_error(data: str):
    """write serialized error with errorbyte set to stdout"""
    sys.stdout.buffer.write(bentoapi.StdoutData(data).serialize(0x01))
    sys.stdout.buffer.flush()


def _execute(code, call):
    """
    load the function's context and then execute it
    """
    context = dict(locals(), **globals())
    context['api']= bentoapi
    byte_code= compile(code, '<inline>', 'exec')
    try:
        exec(byte_code, context, context)
        return eval(call, context) 
    except Exception as e:
        _write_error(str(e)) 


def _main():
    """
    parse function code and call from argument and execute
    """
    todo= sys.argv[1]

    exec_data= json.loads(base64.urlsafe_b64decode(todo.encode()).decode())
    
    call= exec_data['call']
    code= exec_data['code']

    # execute the function and send any return value back
    retval= _execute(code, call)
    if retval:
        bentoapi.send(retval) 


_main()

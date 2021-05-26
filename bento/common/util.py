from functools import wraps
import logging
import sys
import time

def timeit(method):
    """
    Decorator that times how long a function takes
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        start_time= time.time()
        result= method(*args, **kwargs)
        end_time= time.time()
        print("=========================================================")
        print(f"{method.__name__} => {(end_time-start_time)*1000} ms")
        print("=========================================================")

        return result

    return wrapper

def fatal(msg):
    logging.error(msg)
    sys.exit(1)

def read_file(path):
    with open(path) as f:
        data = f.read()
    return data

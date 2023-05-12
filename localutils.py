#!/usr/bin/python3

#profiling
from time import time
from functools import wraps

from flask import request

def getUsername():
    #sample user
    testRemoteUser = "testuser1"
    request.environ['REMOTE_USER'] = testRemoteUser #set value to sample-user

    userName = request.environ.get('REMOTE_USER') #retrieve from request.environ. eg: apache can set this env-value and pass it to flask-app via WSGI
    return userName

#profile helper
def _log(message):
    print('[SimpleTimeTracker] {function_name} {total_time:.3f}'.format(**message))

#simple time profiling. add line @simple_time_tracker(_log) above each function that you want to profile
def simple_time_tracker(log_fun):
    def _simple_time_tracker(fn):
        @wraps(fn)
        def wrapped_fn(*args, **kwargs):
            start_time = time()

            try:
                result = fn(*args, **kwargs)
            finally:
                elapsed_time = time() - start_time

                # log the result
                log_fun({
                    'function_name': fn.__name__,
                    'total_time': elapsed_time,
                })

            return result

        return wrapped_fn
    return _simple_time_tracker

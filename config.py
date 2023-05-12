#!/usr/bin/python3
import os
import localenv

class Config(object):
    #Flask and some of its extensions use the value of the secret key as a cryptographic key, useful to generate signatures or tokens. The Flask-WTF extension uses it to protect web forms against a nasty attack called Cross-Site Request Forgery or CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or localenv.FLASK_SECRET_KEY

    #flask-debug: also enables auto-reload for local file changes
    DEBUG = True

    #pretty-print json output
    JSONIFY_PRETTYPRINT_REGULAR = True

#!/usr/bin/python3
import os
import localenv

flaskDebugInput = os.environ.get('FLASK_DEBUG') or localenv.FLASK_DEBUG
jsonPrettyPrintInput = os.environ.get('FLASK_JSON_PRETTYPRINT') or localenv.FLASK_JSON_PRETTYPRINT

flaskDebug = str(flaskDebugInput).lower() in ['true']
jsonPrettyPrint = str(jsonPrettyPrintInput).lower() in ['true']

class Config(object):
    #Flask and some of its extensions use the value of the secret key as a cryptographic key, useful to generate signatures or tokens. The Flask-WTF extension uses it to protect web forms against a nasty attack called Cross-Site Request Forgery or CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or localenv.FLASK_SECRET_KEY

    #flask-debug: also enables auto-reload for local file changes
    DEBUG = flaskDebug

    #pretty-print json output
    JSONIFY_PRETTYPRINT_REGULAR = jsonPrettyPrint

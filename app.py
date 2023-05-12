#!/usr/bin/python3

#Flask maps HTTP requests to Python functions

#flask class, handle-requests
from flask import Flask, request, render_template, redirect, url_for

#custom config definitions
from config import Config

#sample-form
from remotejobsform import remotejobsui

#contactus
from contactus import contactusui

#local-utilities
from localutils import getUsername

import localenv

#create an instance of the flask class
app = Flask(__name__)

#for apache WSGI
application = app

#debug
app.config.from_object(Config)

#sample ui-form
app.register_blueprint(remotejobsui, url_prefix='/remotejobsui')

#contactus
app.register_blueprint(contactusui, url_prefix='/contactus')

#variables
httpRCok = 200
httpRCbad = 400
httpRCnotfound = 404

devopsContact=localenv.CONTACT

#before request - always run this in the server before anything - logging, any action, monitoring, etc
#@app.before_request
#def before():
#    print("This is executed BEFORE each request.")

#We use the route() decorator to tell Flask what URL should trigger the function. methods specify which HTTP methods are allowed. The default is ['GET']

@app.route('/')
def redirecthome():
    return redirect(url_for('home'))

#redirection for home
@app.route('/home/')
def home():
    username = getUsername()
    return render_template('index.html', title='Home', user=username, appcontact=devopsContact)

@app.errorhandler(404)
def page_not_found(e):
    #return "<h1>404</h1><p>The resource could not be found.</p>", 404
    username = getUsername()
    #ensure http-rc is set to 404
    return render_template('error404.html', title='PageNotFound', user=username, appcontact=devopsContact), httpRCnotfound

#run only when executed in the main file and not when it is imported in some other file
if __name__ == '__main__':
    #run the flask app
    app.run(host='0.0.0.0', port=4015)

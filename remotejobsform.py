#!/usr/bin/python3

#flask stuff
from flask import Blueprint, render_template

#return output in json
import json

#custom-form class
from forms import RemoteJobsForm

#custom config definitions
from config import Config

import localenv

from localutils import getUsername

from jobs_scraper import show_job_list, get_job_list, search_job_list

#ui-form route
remotejobsui = Blueprint('remotejobsui', __name__)

#variables
httpRCok=200
httpRCbad=400
httpRCsvr=500

devopsContact=localenv.CONTACT

try:
  buyMeCoffee = str(localenv.BUY_ME_COFFEE_URL).split("/")[-1]
except:
  buyMeCoffee=None

@remotejobsui.route('/', methods=['GET', 'POST'])
def uiform():
    username = getUsername()

    form = RemoteJobsForm()
    formOutput = {}

    job_details = localenv.JOB_DETAILS
    if form.validate_on_submit():
        keyword_sub = form.searchkeyword.data
        #formOutput = get_job_list(keyword_sub, job_details) #redo job-scraping
        formOutput = search_job_list(keyword_sub) #search from sqlite-db

        return render_template('remotejobs.html', title='Remote Jobs', user=username, form=form, output=formOutput, appcontact=devopsContact, buyMeCoffee=buyMeCoffee)
    else:
        #formOutput = get_job_list(None, job_details)
        formOutput = show_job_list() #search from sqlite-db

        return render_template('remotejobs.html', title='Remote Jobs', user=username, form=form, output=formOutput, appcontact=devopsContact, buyMeCoffee=buyMeCoffee)

    return render_template('remotejobs.html', title='Remote Jobs', user=username, form=form, output=formOutput, appcontact=devopsContact, buyMeCoffee=buyMeCoffee)

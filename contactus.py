#!/usr/bin/python3

#flask stuff
from flask import Blueprint, render_template, url_for

#custom-form class
from forms import ContactForm

from localutils import getUsername

import localenv

from email_sendinblue import sendEmail

#environment attributes
import os

#ui-form route
contactusui = Blueprint('contactusui', __name__)

#variables
httpRCok=200
httpRCbad=400
httpRCsvr=500

appContact = os.environ.get('CONTACT') or localenv.CONTACT

try:
  buyMeCoffee = str(localenv.BUY_ME_COFFEE_URL).split("/")[-1]
except:
  buyMeCoffee=None

#Contact Form
@contactusui.route('/', methods=['GET', 'POST'])
def uiform():
    username = getUsername()

    form = ContactForm()
    formOutput = {}
    if form.validate_on_submit():
        #form-input
        name_sub = form.name.data
        senderemail_sub = form.senderemail.data
        message_sub = form.message.data

        #app-config
        emailsubject = "Remote Jobs Search Engine"
        recipientname = os.environ.get('CONTACTNAME') or localenv.CONTACTNAME
        recipientemail = appContact

        sendEmailRC = sendEmail(emailsubject, senderemail_sub, recipientemail, recipientname, message_sub)
        if (sendEmailRC):
          contactusOutput = "Message sending success. Thank you."
        else:
          contactusOutput = "Sorry, message sending failed. Please try again later. Thank you."

        return render_template('contactus.html', title='Get in touch', user=username, form=form, output=contactusOutput, appcontact=appContact, buyMeCoffee=buyMeCoffee)

    return render_template('contactus.html', title='Get in touch', user=username, form=form, appcontact=appContact, buyMeCoffee=buyMeCoffee)

#!/usr/bin/python3

#forms
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError

import datetime
import re

class RemoteJobsForm(FlaskForm):
    searchkeyword = StringField("Search", render_kw={"placeholder": "Search Keyword"})
    submit = SubmitField('Submit')

    #check if input is string
    def validate_searchkeyword(form, field):
        invalidchars = re.search(r'[@_!#$%^&*()<>?/\|}{~:\d\.]', field.data) #special characters, numbers, and dot
        if (invalidchars):
            print("Please input name in string format")
            raise ValidationError("Please input name in string format")

#######################################

#ContactForm
class ContactForm(FlaskForm):
    name = StringField("Name: ", validators=[DataRequired()], render_kw={"placeholder": "Your Name"})
    senderemail = StringField("Email: ", validators=[DataRequired()], render_kw={"placeholder": "jdoe@gmail.com"})
    message = StringField("Message: ", validators=[DataRequired()])
    submit = SubmitField('Submit')

    #check if input is string
    def validate_name(form, field):
        invalidchars = re.search(r'[@_!#$%^&*()<>?/\|}{~:\d\.]', field.data) #special characters, numbers, and dot
        if (invalidchars):
            print("Please input name in string format")
            raise ValidationError("Please input name in string format")

    #check if input is in email-format
    def validate_senderemail(form, field):
        validregex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        if (not re.fullmatch(validregex, field.data)):
            print("Invalid email address")
            raise ValidationError("Invalid email address")
#######################################

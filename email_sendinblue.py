#!/usr/bin/python3

#############################################################
# Send email using Sendinblue API
#
# Pre-requisites:
# - Create your sendinblue account and generate an API key,
#   from https://app.sendinblue.com/settings/keys/api
#
# VN
#############################################################

#sendinblue library
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

import localenv

def sendEmail(subject: str, senderemail: str, recipientemail: str, recipientname: str, emailcontent: str):
  RC = False

  # Instantiate the client\
  configuration = sib_api_v3_sdk.Configuration()
  configuration.api_key['api-key'] = localenv.APIKEY_SENDINBLUE
  api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

  subject = subject
  sender = {"name":"RemoteJobs","email":senderemail}
  replyTo = {"name":"RemoteJobs","email":senderemail}
  html_content = "<html><body><p>" + emailcontent + "</p></body></html>"
  to = [{"email":recipientemail,"name":recipientname}]
  #params = {"parameter":"My param value","subject":"New Subject"}

  #send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, bcc=bcc, cc=cc, reply_to=replyTo, headers=params, html_content=html_content, sender=sender, subject=subject)
  send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, reply_to=replyTo, html_content=html_content, sender=sender, subject=subject)

  try:
    api_response = api_instance.send_transac_email(send_smtp_email)
    #print(api_response)
    RC = True
  except ApiException as e:
    print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
    RC = False

  return RC

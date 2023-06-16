#!/usr/bin/python3

#flask stuff
from flask import Blueprint, make_response

#rss
from feedgen.feed import FeedGenerator

import pandas as pd

from jobs_scraper import get_jobs_all 

#form route
rss = Blueprint('rss', __name__)

#RSS Subscription
@rss.route('/', methods=['GET'])
def rss_subscription():
  fg = FeedGenerator()
  fg.id('https://remotejobs.duckdns.org')
  fg.title('Remote Jobs Search Engine')
  fg.author({'name':'Lostus Manifestus','email':'lostus.manifestus@gmail.com'})
  fg.description('Consolidates remote jobs from various job sites')
  fg.link(href='/rss/', rel='self')
  fg.language('en')

  #pandas dataframe object
  allJobsDf = pd.DataFrame()

  allJobsDf, allJobsDfRC = get_jobs_all()

  if allJobsDfRC:
    #new rss-item for each job
    for index in allJobsDf.index:
      fe = fg.add_entry(order="append")
      fe.id(allJobsDf["joburl"][index])
      fe.title(allJobsDf["jobname"][index])
      fe.link(href=allJobsDf["joburl"][index])

  response = make_response(fg.rss_str())
  response.headers.set('Content-Type', 'application/rss+xml')

  return response

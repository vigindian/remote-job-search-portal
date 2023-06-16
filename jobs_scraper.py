#!/usr/bin/python3

#web scraping
from bs4 import BeautifulSoup
import requests

import json
import re #regex

import multiprocessing as mp
from functools import partial

#app-db
import sqlite3
#from sqlite3 import Error as sqliteError

#from localutils import simple_time_tracker, _log
import localenv

#data manipulation
import pandas as pd
from IPython.display import HTML

from datetime import datetime

#environment attributes
import os

#ignore SettingWithCopyWarning
pd.options.mode.chained_assignment = None  # default='warn'

debugModeInput = os.environ.get('DEBUG_MODE') or localenv.DEBUG_MODE
debugMode = str(debugModeInput).lower() in ['true']

SEARCH_KEYWORD = os.environ.get('SEARCH_KEYWORD') or localenv.SEARCH_KEYWORD

SQLITE_DATABASE = os.environ.get('SQLITE_DATABASE') or localenv.SQLITE_DATABASE
SQLITE_TABLE = os.environ.get('SQLITE_TABLE') or localenv.SQLITE_TABLE

JOB_SITES = localenv.JOB_SITES

#@simple_time_tracker(_log)
def get_urltext(url):
  """ perform GET request to given URL and return the output """

  headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/112.0'}
  try:
    s = requests.Session()
    r = s.get(url, headers=headers)
    #r = requests.get(url, headers=headers)
    if r.status_code == 200:
      return r.text
    else:
      return None
  except:
    return None

#@simple_time_tracker(_log)
def clean_data(source_data: str):
  """ remove special characters from given input """

  cleandata1 = (re.sub(r'[^a-zA-Z0-9\s]+', '', source_data)).replace("\n","").replace("Remoteco","").strip()
  cleandata = ' '.join(cleandata1.split()) #remove additional white-space
  return cleandata

def sqlite_create_connection(db_file):
  """ create a database connection to a SQLite database """

  conn = None
  try:
    conn = sqlite3.connect(db_file)
    #print(sqlite3.version)
  except sqlite3.Error as e:
    print(e)
  #finally:
  # if conn:
  #   conn.close()

  return conn

def sqlite_exec_query_write(thisconnection: sqlite3.connect, query: str):
  """ execute write operation query in given SQLite database """

  RC = False
  try:
    c = thisconnection.cursor()

    c.execute(query)

    thisconnection.commit()

    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False

  return RC

def sqlite_exec_query_read(thisconnection: sqlite3.connect, query: str):
  """ execute read operation query in given SQLite database """

  RC = False
  df = pd.DataFrame()
  try:
    c = thisconnection.cursor()

    c.execute(query)

    df = pd.DataFrame(c.fetchall(), columns=['joburl','jobname','jobaddedon','location','sourcename'])

    #print (df)

    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False

  return df, RC

def sqlite_job_exists(thisconnection: sqlite3.connect, table: str, url: str):
  """ check if given URL exists in given SQLite table """

  RC = False
  jobExistsRC = False

  try:
    c = thisconnection.cursor()
    
    #print("SELECT joburl from " + str (table) + " where joburl='" + str(url) + "'")
    c.execute("SELECT jobaddedon from " + str (table) + " where joburl='" + str(url) + "'")
    #joburlexists = c.fetchall()
    joburlexists = c.fetchone()

    #job does not exist
    if joburlexists:
      jobExistsRC = True

    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False

  return jobExistsRC, RC

def sqlite_job_add(thisconnection: sqlite3.connect, table: str, url: str, jobname: str, joblocation: str, sourcename: str):
  """ add given job in SQLite """

  RC = False

  try:
    c = thisconnection.cursor()
    
    jobAddedOn = datetime.today().strftime('%Y-%m-%d %H:%M')
    newValue = [url, jobname, jobAddedOn, joblocation, sourcename]
    c.execute("INSERT INTO "+ str(table)+ " VALUES(?,?,?,?,?)", newValue)
    thisconnection.commit()

    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False

  return RC, jobAddedOn

def sqlite_prereq_setup():
  """ sqlite prereq: db and table setup """

  try:
    #create sqlite connection
    connection = sqlite_create_connection(SQLITE_DATABASE)

    #create table
    createTable = sqlite_exec_query_write(connection, '''
          CREATE TABLE IF NOT EXISTS ''' + str(SQLITE_TABLE) +
          '''([joburl] TEXT PRIMARY KEY, [jobname] TEXT, [jobaddedon] TEXT, [location] TEXT, [sourcename] TEXT)
          ''')
    if debugMode:
      if createTable:
        print("create table successful: " + str(SQLITE_TABLE))
      else:
        print("create table not successful: " + str(SQLITE_TABLE))
  #sqlite issue detected
  except:
    connection = None

  return connection

def old_job_cleanup(retention: int):
  """delete jobs older than given days"""

  print("Old job cleanup started...")

  thisCleanupRC = False

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return thisCleanupRC

  #SELECT * from jobdetails where jobaddedon < datetime('now', '-90 days');
  thisJobList, thisJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE) + " where jobaddedon < datetime('now', '-" + str(retention) + " days')")
  print(thisJobList)

  if thisJobListRC:
    for index in thisJobList.index:
      thisJobUrl = thisJobList["joburl"][index]
      print(str(thisJobUrl) + " is older than " + str(retention) + " days. Let's clean it up from our database")
      thisCleanupRC = sqlite_exec_query_write(sqliteConnection, "DELETE from " + str (SQLITE_TABLE) + " where joburl ='" + str(thisJobUrl) + "'")

  return thisCleanupRC

def obsolete_job_cleanup(jobSourceName: str, allJobUrls: list):
  """cleanup obsolete job(s) that have been removed from the source sites"""

  print("Obsolete job cleanup started...")
  #print (allJobUrls)

  thisSourceCleanupRC = False

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return thisSourceCleanupRC

  thisSourceJobList, thisSourceJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE) + " where sourcename='" + str(jobSourceName) + "'")

  if thisSourceJobListRC:
    #print(thisSourceJobList)

    for index in thisSourceJobList.index:
      thisSourceJobUrl = thisSourceJobList["joburl"][index]
      if thisSourceJobUrl not in allJobUrls:
        print(str(thisSourceJobUrl) + " does not exist in source " + str(jobSourceName) + ". Let's clean it up from our database")
        thisSourceCleanupRC = sqlite_exec_query_write(sqliteConnection, "DELETE from " + str (SQLITE_TABLE) + " where joburl ='" + str(thisSourceJobUrl) + "'")

  return thisSourceCleanupRC

#@simple_time_tracker(_log)
#def get_job_details(eachJobUrl: str): #1-argument with pool.map
def get_job_details(eachJobUrl: str, jobSourceName: str):
  """ get job details of individual job-url """

  #sourceName = str(eachJobUrl).split("/")[2] #1-argument passed, so extract source from job-url
  sourceName = jobSourceName #2-arguments passed using partial method, so get it from input

  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  try:
    #check if job already exists in db
    jobExistsRC, jobExistsRCCheck = sqlite_job_exists(sqliteConnection, SQLITE_TABLE, eachJobUrl)

    #add new job into db
    if jobExistsRCCheck and not jobExistsRC:
      if debugMode:
        print("Job Details extraction started for new job: " +str(eachJobUrl))

      #get job details from job-url
      html_text = get_urltext(eachJobUrl)
      if html_text:
        soup = BeautifulSoup(html_text, "html.parser")
      else:
        return None

      jobTitle = soup.find("title").get_text()

      jobTitle = clean_data(jobTitle)

      jobLocation = clean_data("Worldwide")

      jobExistsRC, jobExistsRCCheck = sqlite_job_exists(sqliteConnection, SQLITE_TABLE, eachJobUrl)

      jobAddRC, jobAddedOn = sqlite_job_add(sqliteConnection, SQLITE_TABLE, eachJobUrl, jobTitle, jobLocation, sourceName)
  
      jobDetails["jobUrl"] = eachJobUrl
      jobDetails["jobTitle"] = jobTitle
      jobDetails["jobAddedOn"] = jobAddedOn
      jobDetails["jobLocation"] = jobLocation
  except:
    print("Job Details cannot be extracted")
  finally:
    if sqliteConnection:
      sqliteConnection.close()

  return jobDetails

#@simple_time_tracker(_log)
def get_job_urls(jobUrl, jobUrlFilter, jobUrlHtmlType, jobUrlHtmlFilter, jobExtendPath, jobResultsFilter):
  """ get job urls for given job-site along with its config parameters """

  url = jobUrl + "/" + jobUrlFilter
  html_text = get_urltext(url)
  if html_text:
    soup = BeautifulSoup(html_text, "html.parser")
  else:
    return None

  if debugMode:
      print(soup)

  list_links = []

  thisSection = []
  if jobUrlHtmlType == "class":
    main_section = soup.find("div", {"class": jobUrlHtmlFilter})
  elif jobUrlHtmlType == "section":
    main_section = soup.find("section", {"id": jobUrlHtmlFilter})
  elif jobUrlHtmlType == "script":
    main_section = soup.find("script", {"id": jobUrlHtmlFilter}).get_text()

    #site specific data extraction
    if "trulyremote.co" in jobUrl:
      mainSectionJson = json.loads(main_section)
      try:
        for remoteJob in mainSectionJson["props"]["pageProps"]["initialListings"]:
          remoteJobUrl = remoteJob["fields"]["roleApplyURL"]
          list_links.append(remoteJobUrl)
      except KeyError:
        if debugMode:
          print("WARN: Unable to extract job details from trulyremote.co")
  elif jobUrlHtmlType == "table":
    main_section = soup.find("table", {"id": jobUrlHtmlFilter})

    #site specific data extraction
    if "remoteok.com" in jobUrl:
      for jobItem in main_section.findAll("tr", id=re.compile("job-")):
        for eachHref in jobItem.findAll("a", href=True, itemprop="url"):
          thisSection.append(eachHref)
  else:
    main_section = soup.find(id=jobUrlHtmlFilter)

  #print("THISSECTION: " +str(thisSection))
  if thisSection:
    sections = thisSection
  else:
    # Get sections
    try:
      sections = main_section.findAll("a", href=True)
    except:
      sections = []
      #return None

  #print("SECTIONS: " + str(sections))
  for link in sections:
    thisLink = str(link["href"])
    #print("EACHLINK: " + thisLink)
    if debugMode:
      print(thisLink)

    #filter results with jobResultsFilter keyword
    if jobResultsFilter is not None:
      if jobResultsFilter not in thisLink:
        continue

    # Append to list
    if thisLink.startswith(jobUrl):
      list_links.append(thisLink)

    if jobExtendPath:
      #ignore specific results
      if "categories" in thisLink or "search" in thisLink or "company" in thisLink:
        continue

      # Include all href that do not start with url link but with "/"
      if thisLink.startswith("/"):
        #link_full = jobUrl + thisLink[1:]
        link_full = jobUrl + thisLink
        if debugMode:
          print("adjusted link =", link_full)

        list_links.append(link_full)

    #elif "maps.google.com" not in str(link["href"]):
    #  list_links.append(thisLink)

  return list_links

def get_job_list(searchKeyword: str, moreDetails: bool):
  """ based on the given job-search-keyword and job-sites, perform web-scraping. Get job details of each listing and update in db """

  #print("given searchKeyword is: " + str(searchKeyword))
  if searchKeyword is None:
    searchKeyword = "devops"

  jobDetailsOutput = []
  allJobDetailsOutput = []
  thisSearchKeyword = ""
  allJobUrls = []

  for jobSite in JOB_SITES["jobsites"]:
    jobSiteEnabled = jobSite["enabled"]

    if not jobSiteEnabled:
      continue

    print(jobSite)

    jobUrl = jobSite["url"]
    jobUrlHtmlType = jobSite["htmltype"]
    jobUrlHtmlFilter = jobSite["htmlfilter"]
    jobExtendPath = jobSite["extendPath"]
    jobResultsFilter = jobSite["resultsfilter"]
    jobSourceName = jobSite["name"]

    #reset search-keyword for every job-site
    thisSearchKeyword = searchKeyword

    #custom keyword for specific sites
    if "remotesoftwareengineeringjobs.com" in jobUrl:
      if searchKeyword.lower() == "devops":
        thisSearchKeyword = "Dev Ops"
      elif searchKeyword.lower() == "aws":
        thisSearchKeyword = "AWS"
      elif searchKeyword.lower() == "backend":
        thisSearchKeyword = "Back End"
      else:
        #capitalise first-letter only
        thisSearchKeyword = thisSearchKeyword.capitalize()

    jobUrlFilter = str(jobSite["urlfilter"]).replace("KEYWORD", thisSearchKeyword)

    print("jobUrl: " + jobUrl + ", jobUrlFilter: " + jobUrlFilter + ", jobUrlHtmlType: " + jobUrlHtmlType + ", jobUrlHtmlFilter: " + jobUrlHtmlFilter + ", jobExtendPath: " + str(jobExtendPath) + ", jobResultsFilter: " + str(jobResultsFilter))

    joburls = get_job_urls(jobUrl, jobUrlFilter, jobUrlHtmlType, jobUrlHtmlFilter, jobExtendPath, jobResultsFilter)
    if joburls:
      if debugMode:
        print(joburls)

      #cleanup jobs that do not exist in source
      jobCleanupRC = obsolete_job_cleanup(jobSourceName, joburls)

      #use multi-processing
      # create a process pool that uses all cpus
      with mp.Pool() as pool:
        #all job-urls in 1 array
        #allJobUrls.append(eachJobUrl for eachJobUrl in joburls)

        #jobDetailsOutput = pool.map(get_job_details, joburls) #pool-map with 1 argument

        #pass joburls and source to the function
        jobSourceMapped = partial(get_job_details, jobSourceName=jobSourceName) #pass static argument using partial
        jobDetailsOutput = pool.map(jobSourceMapped, joburls)

        if jobDetailsOutput:
          if debugMode:
            print(jobDetailsOutput)

          allJobDetailsOutput.append(jobDetail for jobDetail in jobDetailsOutput)

        #optional as we use 'with': close the pool
        #pool.close()
    else:
      jobDetailsOutput = [{'Search Results': 'Sorry, no jobs found'}]

  #return allJobDetailsOutput
  df = pd.DataFrame(allJobDetailsOutput)
  return df

def html_format_output(dfInput):
  """ convert given df-input to HTML format """

  #sort values in descending order based on job-added-date
  #dfInput.sort_values(by='jobaddedon', ascending = False, inplace = True) #redundant as we sort using javascript

  #format role column as link from url column
  dfInput["Role"] = "<a href='" + dfInput['joburl'] + "' target='_blank' rel='noopener noreferrer' style='text-decoration:none;'>" + dfInput['jobname'] + "</a>"

  dfInput = dfInput[['Role','location','jobaddedon']] #re-arrange the columns

  dfInput.rename(columns={'location': 'Location', 'jobaddedon': 'Posted'}, inplace=True) #rename some columns

  #css style
  outputFormat = localenv.OUTPUT_FORMAT

  #append output-format after table for javascript formatting; add <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet"> to base.html
  dfOutput = dfInput.to_html(classes='df', table_id="table", render_links=True, escape=False, index=False) + outputFormat

  return HTML(dfOutput)

def search_job_list(searchKeyword: str):
  """ search given job-name in database - obsoleted by javascript for table """

  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  currentJobList, currentJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE) + " where jobname like '%" + str(searchKeyword) + "%'")
  #df = pd.DataFrame.from_records(data = currentJobList)
  df = currentJobList

  finalOutput = html_format_output(df)

  return finalOutput

def get_jobs_all():
  """ Get all jobs from database """

  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  currentJobList, currentJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE))

  return currentJobList, currentJobListRC

def show_job_list():
  """ show job list in HTML format, to display in webpage """

  try:
    currentJobList, currentJobListRC = get_jobs_all()
    #df = pd.DataFrame.from_records(data = currentJobList)
    df = currentJobList

    finalOutput = html_format_output(df)
  except:
    finalOutput = None

  return finalOutput

if __name__ == '__main__':

  searchKeyword = SEARCH_KEYWORD
  moreDetails = localenv.JOB_DETAILS
  retentionDays = os.environ.get('RETENTION_DAYS') or localenv.RETENTION_DAYS

  #cleanup old jobs from the database
  old_job_cleanup(retentionDays)

  #perform job-scraping from multiple sources
  get_job_list(searchKeyword, moreDetails)

  #currentJobsInDB = show_job_list()
  #print(currentJobsInDB)

  #searchJobs = search_job_list("devops")
  #print(searchJobs)

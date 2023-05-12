#!/usr/bin/python3

from bs4 import BeautifulSoup
import requests

import json
import re #regex

import multiprocessing as mp

import sqlite3
#from sqlite3 import Error as sqliteError

from localutils import simple_time_tracker, _log
import localenv

import pandas as pd
from IPython.display import HTML

from datetime import datetime

debugMode = localenv.DEBUG_MODE

SEARCH_KEYWORD = localenv.SEARCH_KEYWORD

SQLITE_DATABASE = localenv.SQLITE_DATABASE
SQLITE_TABLE = localenv.SQLITE_TABLE

JOB_SITES = localenv.JOB_SITES

# create empty dict
dict_href_links = {}

@simple_time_tracker(_log)
def get_urltext(url):
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

@simple_time_tracker(_log)
#remove special characters
def clean_data(source_data: str):
  cleandata1 = (re.sub(r'[^a-zA-Z0-9\s]+', '', source_data)).replace("\n","").strip()
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
    #    if conn:
    #        conn.close()

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

    df = pd.DataFrame(c.fetchall(), columns=['joburl','jobname','jobaddedon'])
    #print (df)

    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False

  return df, RC

def sqlite_job_exists(thisconnection: sqlite3.connect, table: str, url: str, jobname: str):
  """ check if given URL exists in given SQLite table """
  RC = False
  jobExistsRC = False

  try:
    c = thisconnection.cursor()
    
    #print("SELECT joburl from " + str (table) + " where joburl='" + str(url) + "'")
    c.execute("SELECT jobaddedon from " + str (table) + " where joburl='" + str(url) + "'")
    #joburlexists = c.fetchall()
    joburlexists = c.fetchone()
    #insert into sqlite if job does not exist
    if not joburlexists:
      print("Job does not exist in db")
      jobAddedOn = datetime.today().strftime('%Y-%m-%d')
      newValue = [url, jobname, jobAddedOn]
      c.execute("INSERT INTO "+ str(table)+ " VALUES(?,?,?)", newValue)
      thisconnection.commit()
    #job already exists in db
    else:
      print("Job exists in db")
      #extract only the value
      jobAddedOn = joburlexists[0]
      jobExistsRC = True
    
    RC = True
  except sqlite3.Error as e:
    print(e)
    RC = False
    
  return jobExistsRC, RC, jobAddedOn

def sqlite_prereq_setup():
  #sqlite prereq: db and table setup
  try:
    #create sqlite connection
    connection = sqlite_create_connection(SQLITE_DATABASE)

    #create table
    createTable = sqlite_exec_query_write(connection, '''
          CREATE TABLE IF NOT EXISTS ''' + str(SQLITE_TABLE) +
          '''([joburl] TEXT PRIMARY KEY, [jobname] TEXT, [jobaddedon] TEXT)
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

@simple_time_tracker(_log)
def get_job_details(eachJobUrl):
  html_text = get_urltext(eachJobUrl)
  if html_text:
    soup = BeautifulSoup(html_text, "html.parser")
  else:
    return None

  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  try:
    #print("Job Details extraction started")
    jobTitle = soup.find("title").get_text()

    jobTitle = clean_data(jobTitle)

    jobExistsRC, jobExistsRCCheck, jobAddedOn = sqlite_job_exists(sqliteConnection, SQLITE_TABLE, eachJobUrl, jobTitle)
  
    jobDetails["jobUrl"] = eachJobUrl
    jobDetails["jobTitle"] = jobTitle
    jobDetails["jobAddedOn"] = jobAddedOn
  except:
    print("Job Details cannot be extracted")
  finally:
    if sqliteConnection:
      sqliteConnection.close()

  return jobDetails

@simple_time_tracker(_log)
def get_job_urls(jobUrl, jobUrlFilter, jobUrlHtmlType, jobUrlHtmlFilter, jobExtendPath, jobResultsFilter):
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
      for remoteJob in mainSectionJson["props"]["pageProps"]["initialListings"]:
        remoteJobUrl = remoteJob["fields"]["roleApplyURL"]
        list_links.append(remoteJobUrl)
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
    #thisLink = str(link[0]["href"])
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
  print("given searchKeyword is: " + str(searchKeyword))
  if searchKeyword is None:
    searchKeyword = "devops"

  jobDetailsOutput = []
  allJobDetailsOutput = []
  thisSearchKeyword = ""

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
      print(joburls)

      #traditional for loop
      #for eachJobUrl in joburls:
      #  jobDetails = get_job_details(eachJobUrl)
      #  if jobDetails:
      #    print(jobDetails)

      #use multi-processing
      #pool = mp.Pool(mp.cpu_count())
      # create a process pool that uses all cpus
      with mp.Pool() as pool:
        jobDetailsOutput = pool.map(get_job_details, joburls)
        #jobDetailsOutput.append(pool.map(get_job_details, joburls))
        #if jobDetailsOutput and debugMode:
        if jobDetailsOutput:
          print(jobDetailsOutput)
          allJobDetailsOutput.append(jobDetail for jobDetail in jobDetailsOutput)

        #optional as we use 'with': close the pool
        pool.close()
    else:
      jobDetailsOutput = [{'Search Results': 'Sorry, no jobs found'}]

  #return allJobDetailsOutput
  df = pd.DataFrame(allJobDetailsOutput)
  return df

def html_format_output(inputdf):
  #sort values in descending order based on job-added-date
  inputdf.sort_values(by='jobaddedon', ascending = False, inplace = True)

  #css style
  outputFormat = localenv.OUTPUT_FORMAT
  outputdf = HTML(outputFormat + inputdf.to_html(classes='df', render_links=True, escape=False, index=False))

  return outputdf

def search_job_list(searchKeyword: str):
  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  currentJobList, currentJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE) + " where jobname like '%" + str(searchKeyword) + "%'")
  df = pd.DataFrame.from_records(data = currentJobList)

  finalOutput = html_format_output(df)

  return finalOutput

def show_job_list():
  jobDetails = {}

  sqliteConnection = sqlite_prereq_setup()
  if sqliteConnection is None:
    return jobDetails

  currentJobList, currentJobListRC = sqlite_exec_query_read(sqliteConnection, "SELECT * from " + str (SQLITE_TABLE))
  df = pd.DataFrame.from_records(data = currentJobList)

  finalOutput = html_format_output(df)

  return finalOutput

if __name__ == '__main__':

  searchKeyword = SEARCH_KEYWORD
  moreDetails = localenv.JOB_DETAILS
  get_job_list(searchKeyword, moreDetails)

  #currentJobsInDB = show_job_list()
  #print(currentJobsInDB)

  #searchJobs = search_job_list("devops")
  #print(searchJobs)

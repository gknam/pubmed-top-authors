# -*- coding: utf-8 -*-

import ast
import asyncio
import collections
import datetime
import gzip
import hashlib
import logging
import os
import random
import re
import time
import socket
import string
import urllib, json
import xml.etree.ElementTree as ET

from ftplib import FTP
from glob import glob
from unidecode import unidecode
from urllib.request import urlretrieve
from operator import itemgetter


### Note 1 ###
# Each time a file is read or written, ".replace('\x00', '')" is added to
# prevent null bytes ('\x00') being written and remove them if already written
#
## Note 2 ###
# Functions are marked with "original", "extracts", or "both". This shows
# whether the function is required in both versions or only one of them.
#
# The versions are called so because article details are fetched either
# directly from Pubmed using eFetch ("original") or
# from server database which contains extracts from Pubmed database
# of NCBI ("extracts").
#
# The only functions whose names indicate these versions are getFullRecs_ori
# and getFullRecs_ext.
##############

# tool name and developer's email
# (NCBI will contact the developer with this in case there is a problem
# (http://bit.ly/2whcAzM))
tool = "pubmedTopAuthors"
email = "simon_nam@hotmail.com"

# dbUpdating status indicator
dbUpdating = False

# make FTP job or download quit after 30 seconds
socket.setdefaulttimeout(30)

# start logging error messages
tempLog = 'logs_others/temp.log'
logging.basicConfig(level=logging.DEBUG, filename=tempLog)

# xml directories
# "xml_extracts/": For "extracts" mode. For XMLs downloaded from Pubmed's FTP site.
# "xml_original/": For "original mode. For XMLs downloaded via efetch.
xml_extracts_dir = "xml_extracts/"
xml_original_dir = "xml_original/"

# Error logs to check when crashed
upDbFail_part1_file = "logs_updateDb/updateDbFailed_part1.log"
upDbFail_part2_file = "logs_updateDb/updateDbFailed_part2.log"

# remove pre-existing XML files
for x in (glob(xml_extracts_dir + "*.xml.gz") + glob(xml_original_dir + "*.xml")):
    os.remove(x)

def getPmids(term, retmax, reldate, searchOption):
    """
    Get PMIDs for term.

    version required by: both
    """

    retmax = round(int(retmax))
    reldate = round(int(reldate))

    if searchOption == "Author":
        term += "[au]"
    elif searchOption == "Keyword":
        pass

    # maximum number of articles to retrieve
    retmax_limit = 100000

    # subset of articles to start from
    # (e.g. if retstart is 0, articles are fetched from the beginning of the stack.
    # if retstart is 10, first 10 articles in the stack are ignored.
    retstart = 0

    pmids = []
    while retstart < retmax:

        retmax_part = retmax if retmax <=retmax_limit else retmax_limit

        # retrieve PMIDs
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={}&retmax={}&retstart={}&reldate={}&tool={}&email={}&datetype=pdat&sort=pub+date".format(urllib.parse.quote(term), urllib.parse.quote(str(retmax_part)), urllib.parse.quote(str(retstart)), urllib.parse.quote(str(reldate)), urllib.parse.quote(tool), urllib.parse.quote(email))
        feed = urllib.request.urlopen(url)
        obj = json.loads(feed.read().decode("utf-8"))

        # note PMIDs
        pmids_part = []
        for pmid_part in obj["esearchresult"]["idlist"]:
            pmids_part.append(pmid_part)
        pmids = pmids + pmids_part

        if len(pmids_part) < retmax_limit:
            break

        retstart += retmax_limit

    return pmids

def getFullRecs_ext(db, pmids):
    """
    For each PMID, get full records from database

    version required by: extracts
    """

    # file name
    rPmids_file = "logs_others/pmidsRejected.txt"

    # info for a summary report to be given in the front-end.
    # pmidsInc_len: number of articles checked (after excluding inappropriate ones)
    # pubYear_oldest: publication year for oldest article fetched.

    pmidsAll_len = len(pmids)
    pmidsInc_len = 0
    pubYear_oldest = 0

    # get records from Pubmed
    # record[0]: author (essential info)
    # record[1]: allAuthors
    # record[2]: year (essential info)
    # record[3]: aTitle
    # record[4]: journal (essential info)
    # record[5]: journalNonAbbr
    # record[6]: journalVol
    # record[7]: journalIss
    # record[8]: pageNum
    # record[9]: pmidLink
    # record[10]: doiLink

    record = [[], [], [], [], [], [], [], [], [], [], []]
    records = {}

    if not pmids:
        return {}

    # convert pmids list into string
    pmids_str = '('
    for i in range(pmidsAll_len):
        if i + 1 == pmidsAll_len:
            pmids_str += str(pmids[i]) + ')'
        else:
            pmids_str += str(pmids[i]) + ', '

    # query db with pmids
    dbRow = dbConExe(db, "SELECT pmid, fname, lname, initials, pyear, journal, \
                     journalNonAbbr, article, journalVol, journalIss, pageNum, doi \
                     FROM medline WHERE pmid in {}".format(pmids_str))

    pmidsInc_len = len(dbRow)

    # Start recording rejected pmids
    with open(rPmids_file, "a") as f:

        for dbRec in dbRow:
            # reset record
            record = [[], [], [], [], [], [], [], [], [], [], []]

            # get pmid
            pmid = str(dbRec["pmid"])

            # get author names and initials

            fnameList = dbRec["fname"].split("___")
            lnameList = dbRec["lname"].split("___")
            initialsList = dbRec["initials"].split("___")

            # reject article if error in author name parsing
            # (note: author names were added to db only if both first and last
            # names were available)
            if len(fnameList) != len(lnameList):

                if len(fnameList) > len(lnameList):
                    nameWithTripleUnderscores = "First name of one or more authors"
                else:
                    nameWithTripleUnderscores = "Last name of one or more authors"

                # log error into file
                f.write("pmid {}: {} contains triple underscores\n".format(pmid, nameWithTripleUnderscores).replace('\x00', ''))
                break

            # fetch info

            # 1. author names
            authors = []
            allAuthors = ''
            count = 0
            for lname, fname, initials in zip(lnameList, fnameList, initialsList):
                # get full names as a list (code based on https://stackoverflow.com/a/11703083)
                authors.append(lname + ', ' + fname)

                # get full names as a string
                ## when there are multiple authors
                authors_num = len(lnameList)
                if authors_num > 1:
                    allAuthors += '& ' + lname + ', ' + initials + ' ' \
                        if count == authors_num - 1 \
                        else lname + ', ' + initials + ', '
                ## when there is one author
                else:
                    allAuthors = lname + ', ' + initials + ' '

                count += 1

            for author in authors:
                record[0].append(author)

            record[1].append(allAuthors)

            # 2. publication year
            year = dbRec["pyear"]
            record[2].append(year)

            # note publication year of oldest article in record (i.e. in current session)
            if pubYear_oldest:
                if int(year) <= pubYear_oldest:
                    pubYear_oldest = int(year)
            else:
                pubYear_oldest = int(year)

            # 3. journal title
            journal = dbRec["journal"]
            record[4].append(journal)

            # 4. pubmed link
            pmidLink = "https://www.ncbi.nlm.nih.gov/pubmed/" + pmid
            record[9].append(pmidLink)

            # 5. doi link
            doi = dbRec["doi"]
            doiLink = '' if doi == None else "http://dx.doi.org/" + doi
            record[10].append(doiLink)

            # 6. article title
            article = dbRec["article"]
            if article == None:
                article = ''
            record[3].append(article)

            # 7. journal title (non-abbreviated)
            journalNonAbbr = dbRec["journalNonAbbr"]
            if journalNonAbbr == None:
                journalNonAbbr = ''
            record[5].append(journalNonAbbr)

            # 8. journal volume
            journalVol = dbRec["journalVol"]
            if journalVol == None:
                journalVol = ''
            record[6].append(journalVol)

            # 9. journal issue
            journalIss = dbRec["journalIss"]
            if journalIss == None:
                journalIss = ''
            record[7].append(journalIss)

            # 10. page number
            pageNum = dbRec["pageNum"]
            if pageNum == None:
                pageNum = ''
            record[8].append(pageNum)

            # add key info to records
            # make sure there is no empty field
            if [] not in record:
                # add record to records
                for author in record[0]:

                    # put together full reference info
                    ref = []

                    for i in range(len(record)):
                        if i in {0, 4}:
                            continue
                        ref.append(record[i][0])

                    # author
                    if author not in records:
                        records[author] = [{"total": 1}, {"journals": {}}, {"years": {}}]
                    else:
                        records[author][0]["total"] += 1

                    # journal title (code from http://stackoverflow.com/a/14790997)
                    if not any(journal == d for d in records[author][1]["journals"]):
                        records[author][1]["journals"][journal] = [1, [ref]]
                    else:
                        journalRec = records[author][1]["journals"][journal]
                        journalRec[0] += 1
                        journalRec[1].append(ref)

                    # publication year (code from http://stackoverflow.com/a/14790997)
                    if not any(year == d for d in records[author][2]["years"]):
                        records[author][2]["years"][year] = [1, [ref]]
                    else:
                        yearRec = records[author][2]["years"][year]
                        yearRec[0] += 1
                        yearRec[1].append(ref)

        # Merge two author records if their names are spelled the same way, but in
        # different letter cases (e.g. Mike vs mike).
        #TODO: Should this be done in xmlToDb function?
        mergeSimilarSpelledAuthors(records)
    
        # sort reference info
        sortRefInfo(records)

        # sort whole records
        records = collections.OrderedDict(sorted(records.items()))

        return records, pmidsAll_len, pmidsInc_len, pubYear_oldest

def getFullRecs_ori(pmids):
    """
    Get full records from PMID

    version required by: original
    """

    # info for a summary report to be given in the front-end.
    # pmidsInc_len: number of articles checked (after excluding inappropriate ones)
    # pubYear_oldest: publication year for oldest article fetched.

    pmidsAll_len = len(pmids)
    pmidsInc_len = pmidsAll_len
    pubYear_oldest = 0 # today's date

    # get records from Pubmed
    # record[0]: author (essential info)
    # record[1]: allAuthors
    # record[2]: year (essential info)
    # record[3]: aTitle
    # record[4]: journal (essential info)
    # record[5]: journalNonAbbr
    # record[6]: journalVol
    # record[7]: journalIss
    # record[8]: pageNum
    # record[9]: pmidLink
    # record[10]: doiLink

    record = [[], [], [], [], [], [], [], [], [], [], []]
    records = {}

    if not pmids:
        return {}

    pmids = ','.join(pmids)

    # get records from Pubmed
    # note: To minimise use of memory, the requested XML will be saved as file
    # and each element will be accessed iteratively (instead of directly
    # loading the whole XML into memory)

    # 1. using GET method
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&retmode=xml&tool={}&email={}".format(pmids, urllib.parse.quote(tool), urllib.parse.quote(email))
        xml, headers = urllib.request.urlretrieve(url, filename=generateXmlFilename())
    # 2. using POST method (if pmids is too long)
    except urllib.error.HTTPError:
        ids = urllib.parse.urlencode({"id": pmids, "tool": tool, "email": email}).encode("utf-8")
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml"
        xml, headers = urllib.request.urlretrieve(url, filename=generateXmlFilename(), data=ids)

    # for checking articles to exclude
    rt_discardCurrent = {"ErratumFor", "PartialRetractionOf", "ReprintIn", \
                    "RepublishedIn", "OriginalReportIn", "RetractionIn", \
                    "RetractionOf"}

    pt_discardCurrent = {"Retracted Publication",  "Retraction of Publication", \
                         "Published Erratum"}

    with open(xml, "r") as f:

        # remove xml file to save space
        os.remove(xml)

        # read in XMl and get root
        xmlIterTree, root = getXmlIterTreeAndRoot(f)

        # note key info for each article
        for event, elem in xmlIterTree:
            if event == 'end':
                if elem.tag == "MedlineCitation":
                    # reset record
                    record = [[], [], [], [], [], [], [], [], [], [], []]

                    # ↓↓↓ skip article if it should be excluded: begin ↓↓↓ #

                    cc_list = elem.findall('.//CommentsCorrectionsList/CommentsCorrections')
                    pt_list = elem.findall('.//PublicationTypeList/PublicationType')

                    skipArticle = False

                    # check "CommentsCorrections" element
                    for cc in cc_list:
                        rt = cc.get("RefType")

                        # article has been retracted or replaced by
                        # later-published version, is a retraction notification
                        # or a patient summary article
                        if rt in rt_discardCurrent:
                            skipArticle = True

                    # check "PublicationType" element
                    for ptElement in pt_list:
                        pt = ptElement.text

                        # article has been retracted or is a retraction notification
                        if pt in pt_discardCurrent:
                            skipArticle = True

                    if skipArticle:
                        pmidsInc_len -= 1
                        continue

                    # ↑↑↑ skip article if it should be excluded: end ↑↑↑ #

                    # 1. get essential info
                    # note authors
                    fname = ''
                    lname = ''
                    initials = ''
                    author = ''
                    allAuthors = ''
                    try:
                        authorsInfo = elem.findall('.//AuthorList/Author[@ValidYN="Y"][LastName][ForeName]')
                        for i in range(len(authorsInfo)):
                            au = authorsInfo[i]

                            lname = toASCII(dashToSpace(au.find("LastName").text))
                            fname = toASCII(dashToSpace(au.find("ForeName").text))
                            author = lname + ', ' + fname
                            record[0].append(author)

                            # this is extra info (i.e. not essential)
                            try:
                                initials = toASCII(dashToSpace(' '.join([i + '.' for i in au.find("Initials").text])))
                            except:
                                initials = toASCII(dashToSpace(' '.join([i[0] + '.' for i in fname.split()])))

                            try:
                                authorsInfo_len = len(authorsInfo)
                                # when there are multiple authors
                                if authorsInfo_len > 1:
                                    allAuthors += '& ' + lname + ', ' + initials + ' ' \
                                        if i == authorsInfo_len - 1 \
                                        else lname + ', ' + initials + ', '
                                # when there is one author
                                else:
                                    allAuthors = lname + ', ' + initials + ' '
                            except:
                                pass
                    except:
                        pass

                    if not author:
                        continue

                    try:
                        record[1].append(allAuthors)
                    except:
                        pass

                    # note publication year
                    year = ''
                    for pd in elem.findall('.//Article/Journal/JournalIssue/PubDate'):
                        try:
                            year = pd.find("Year").text
                        except:
                            try:
                                medlineDate = pd.find("MedlineDate").text
                                try:
                                    year = str(int(medlineDate[:4]))
                                # extract 4-digit number (code from https://stackoverflow.com/a/4289557)
                                except:
                                    try:
                                        year = str([int(s) for s in medlineDate.split() if s.isdigit() and len(s) == 4][0])
                                    except:
                                        continue
                            except:
                                continue

                        record[2].append(year)

                        # note publication year of oldest article in record (i.e. in current XML)
                        if pubYear_oldest:
                            if int(year) <= pubYear_oldest:
                                pubYear_oldest = int(year)
                        else:
                            pubYear_oldest = int(year)

                    if not year:
                        continue

                    # note journal title
                    journal = ''
                    try:
                        for jAbbr in elem.findall('MedlineJournalInfo/MedlineTA'):

                            try:
                                journal = toASCII(dashToSpace(jAbbr.text))
                            except:
                                continue

                            record[4].append(journal)
                    except:
                        continue

                    if not journal:
                        continue

                    # 2. get extra info

                    # 2.1 get pubmed link
                    pmid = ''
                    pmidLink = ''
                    try:
                        pmid = elem.find('PMID').text
                    except:
                        pass

                    if pmid:
                        pmidLink = "https://www.ncbi.nlm.nih.gov/pubmed/" + pmid
                        record[9].append(pmidLink)

                    # 2.2 get article title, journal's non-abbreviated title,
                    # volume, issue, page numbers and DOI link
                    aTitle = ''
                    journalNonAbbr = ''
                    journalVol = ''
                    journalIss = ''
                    doiLink = ''

                    for a in elem.findall('.//Article'):

                        # doi link
                        doi = ''
                        doiLink = ''
                        try:
                            doi = a.find('ELocationID[@EIdType="doi"][@ValidYN="Y"]').text
                        except:
                            pass

                        if doi:
                            doiLink = "http://dx.doi.org/" + doi
                            record[10].append(doiLink)

                        # article title
                        try:
                            aTitle = toASCII(dashToSpace(a.find('ArticleTitle').text))
                        except:
                            pass

                        # If aTitle is None, revert it back to ''
                        if aTitle == None:
                            aTitle = ''

                        record[3].append(aTitle)

                        # journal info , volume and issue
                        for j in a.findall('Journal'):

                            # non-abbreviated title
                            try:
                                journalNonAbbr = toASCII(dashToSpace(j.find('Title').text))
                            except:
                                journalNonAbbr = journal
                            if journalNonAbbr == None:
                                journalNonAbbr = ''

                            record[5].append(journalNonAbbr)

                            for ji in j.findall('JournalIssue'):
                                # volume
                                try:
                                    journalVol = ji.find('Volume').text
                                except:
                                    pass

                                if journalVol == None:
                                    journalVol = ''

                                record[6].append(journalVol)

                                # issue
                                try:
                                    journalIss = ji.find('Issue').text
                                except:
                                    pass

                                if journalIss == None:
                                    journalIss = ''

                                record[7].append(journalIss)

                        # page numbers
                        pageNum = ''
                        try:
                            pageNum = a.find('Pagination/MedlinePgn').text
                        except:
                            pass

                        if pageNum == None:
                            pageNum = ''

                        record[8].append(pageNum)

                    # add key info to records
                    # make sure there is no empty field
                    if [] not in record:
                        # add record to records
                        for author in record[0]:

                            # put together full reference info
                            ref = []

                            for i in range(len(record)):
                                if i in {0, 4}:
                                    continue
                                ref.append(record[i][0])

                            # author
                            if author not in records:
                                records[author] = [{"total": 1}, {"journals": {}}, {"years": {}}]
                            else:
                                records[author][0]["total"] += 1

                            # journal title (code from http://stackoverflow.com/a/14790997)
                            if not any(journal == d for d in records[author][1]["journals"]):
                                records[author][1]["journals"][journal] = [1, [ref]]
                            else:
                                journalRec = records[author][1]["journals"][journal]
                                journalRec[0] += 1
                                journalRec[1].append(ref)

                            # publication year (code from http://stackoverflow.com/a/14790997)
                            if not any(year == d for d in records[author][2]["years"]):
                                records[author][2]["years"][year] = [1, [ref]]
                            else:
                                yearRec = records[author][2]["years"][year]
                                yearRec[0] += 1
                                yearRec[1].append(ref)

                    elem.clear()
                root.clear()
    
    # Merge two author records if their names are spelled the same way, but in
    # different letter cases (e.g. Mike vs mike).
    mergeSimilarSpelledAuthors(records)

    # sort reference info
    sortRefInfo(records)

    records = collections.OrderedDict(sorted(records.items()))

    return records, pmidsAll_len, pmidsInc_len, pubYear_oldest

def topAuthorsRecs(records, pmidsAll_len, pmidsInc_len, pubYear_oldest, numTopAuthors):
    """
    get records of authors with most publication

    version required by: both
    """
    global dbUpdating

    # max plot dimensions (for equalising plot dimensions in the browser)
    # "scripts_suggestJS.js" file --> "chartDim" function --> "dataCount" variable
    authorCountMax = numTopAuthors # number of top authors to find
    journalCountMax = 0
    yearCountMax = 0
    # "scripts_suggestJS.js" file --> "chartDim" function --> "dataStrLengthMax" variable
    authorStrLenMax = 0
    journalStrLenMax = 0
    yearStrLenMax = 0

    # get total number of publication for each author
    totals = {}
    for author, info in records.items():
        total = info[0]['total']
        if total in totals:
            totals[total].append(author)
        else:
            totals[total] = [author]
    totals = collections.OrderedDict(sorted(totals.items(), reverse=True))

    # get records of authors with most publication
    topAuthorsRecs = {}
    topAuthorsRecsLen = 0
    for total, authors in totals.items():
        for author in authors:
            if topAuthorsRecsLen < authorCountMax and topAuthorsRecsLen < len(records):
                topAuthorsRecsLen += 1
                if total in topAuthorsRecs:
                    topAuthorsRecs[total].append({author: records[author]})
                else:
                    topAuthorsRecs[total] = [{author: records[author]}]
            else:
                break

    topAuthorsRecs = collections.OrderedDict(sorted(topAuthorsRecs.items()))

    # sort the top authors' records
    for total, recs in topAuthorsRecs.items():
        for rec in range(len(recs)):
            for author, info in topAuthorsRecs[total][rec].items():

                # sort journal records
                journals = topAuthorsRecs[total][rec][author][1]["journals"]
                # by keys
                journals = collections.OrderedDict(sorted(journals.items()))
                # then by values (code from https://goo.gl/1ikwL0)
                # another way is to convert dict to sorted list of tuples
                # (http://stackoverflow.com/a/613218)
                journals = collections.OrderedDict(sorted(journals.items(), key=lambda t: t[1][0]))
                topAuthorsRecs[total][rec][author][1]["journals"] = journals

                # sort publication year records
                years = topAuthorsRecs[total][rec][author][2]["years"]
                # by keys
                years = collections.OrderedDict(sorted(years.items()))
                topAuthorsRecs[total][rec][author][2]["years"] = years

                # fill in missing years with 0
                # (e.g. if record exists for only 2014 and 2016, add {'2015': 0})
                # (referred to code from https://stackoverflow.com/a/16974075)
                yearS = topAuthorsRecs[total][rec][author][2]["years"]
                yearsFillGap = list(yearS.items())
                if len(yearS) > 1:
                    startYr = int(yearsFillGap[0][0])
                    for i in range(0, len(yearsFillGap)):
                        endYr = int(yearsFillGap[i][0])
                        if endYr - startYr > 1:
                            missingYrs = set(range(startYr + 1, endYr))
                            startYrIndex = list(yearS).index(str(startYr))
                            for yr in missingYrs:
                                yearsFillGap.insert(startYrIndex + 1, (str(yr), [0, [[]]]))
                                yearS = dict(yearsFillGap)
                                topAuthorsRecs[total][rec][author][2]["years"] = yearS
                        startYr = endYr

                # max records of journals and years
                if len(journals) > journalCountMax:
                    journalCountMax = len(journals)
                if len(years) > yearCountMax:
                    yearCountMax = len(years)

                # max string lengths of author names, journal names and years
                if len(author) > authorStrLenMax:
                    authorStrLenMax = len(author)
                if max(map(len, journals)) > journalStrLenMax:
                    journalStrLenMax = max(map(len, journals))
                if max(map(len, years)) > yearStrLenMax:
                    yearStrLenMax = max(map(len, years))

    # add info for max plot dimensions
    topAuthorsRecs.update({"dataCount": {"authorCountMax": authorCountMax, "journalCountMax": journalCountMax, "yearCountMax": yearCountMax}})
    topAuthorsRecs.update({"dataStrLengthMax": {"authorStrLenMax": authorStrLenMax, "journalStrLenMax": journalStrLenMax, "yearStrLenMax": yearStrLenMax}})
    # add info for summary reports
    topAuthorsRecs.update({"numbersOfArticles": [pmidsAll_len, pmidsInc_len]})
    topAuthorsRecs.update({"oldestPubyearChecked": pubYear_oldest})
    topAuthorsRecs.update({"dbUpdating": dbUpdating})

    return topAuthorsRecs

def toASCII(s):
    """
    Converts extended-ASCII character to regular ASCIIi character
    (e.g. ä --> a)

    Codes are based on those at following pages
    https://stackoverflow.com/a/2633310
    https://stackoverflow.com/a/518232

    version required by: both
    """

    # if all chracters are regular ASCII, return original string
    if all(ord(c) < 128 for c in s):
        return s

    # otherwise, decode with unidecode
    d = unidecode(s)

    return d




def removeFromLog(logName, key):
    """
    Removes key from log

    version required by: extracts
    """
    with open(logName, "a+") as f:
        f.seek(os.SEEK_SET)
        log = f.read().replace('\x00', '')
    if log:
        log = ast.literal_eval(log)
        if key in log:
            log.pop(key)
            with open(logName, "w") as f:
                f.write(str(log).replace('\x00', ''))

def call_in_background(target, db, *, loop=None, executor=None):
    """
    code from http://www.curiousefficiency.org/posts/2015/07/asyncio-background-calls.html

    Schedules and starts target callable as a background task.

    If not given, *loop* defaults to the current thread's event loop
    If not given, *executor* defaults to the loop's default executor

    Returns the scheduled task.

    version required by: extracts
    """

    if loop is None:
        # code from https://stackoverflow.com/a/25066490/7194743
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop = asyncio.get_event_loop()
    if callable(target):
        return loop.run_in_executor(executor, target, db)
    raise TypeError("target must be a callable, "
                    "not {!r}".format(type(target)))

def ftpJob(ftpAddress, directory, *args):
    """
    Login to Pubmed's FTP server and given directory, then run commands.

    Upon each failure, full Exception message (i.e. error message) is logged
    and ftpJob is retried.

    Return a tuple: First value indicates whether FTP loggin was successful.
                    Second value is the result of the command if "returnVal"
                        assignment was indicated in args.

    version required by: extracts
    """

    ftp = ""
    ftpJobDone = False
    failedFtpJobs_file = "logs_others/failedFtpJobs.txt"
    failedFtpJobs = logToDic(failedFtpJobs_file)
    command = str(args)
    count = 0
    while not ftpJobDone:
        count += 1
        try:
            ftp = FTP(ftpAddress)
            ftp.login()
            ftp.cwd(directory)

            returnVal = None

            # code from https://stackoverflow.com/a/1463370/7194743
            ldict = locals()
            for arg in args:
                exec(arg, globals(), ldict)
            returnVal = ldict['returnVal']

            ftpQuit(ftp)

            ftpJobDone = True
        except:
            ftpQuit(ftp)

            open(tempLog, 'w').close()
            logging.exception("ftpJob failed:")

            with open(tempLog, "r") as f:
                e = f.read().replace('\x00', '').splitlines()[-1]

            # log full error message
            if command not in failedFtpJobs:
                failedFtpJobs[command] = {e: 1}
            elif e not in failedFtpJobs[command]:
                failedFtpJobs[command][e] = 1
            else:
                failedFtpJobs[command][e] += 1

            with open(failedFtpJobs_file, "w") as f:
                 f.write(str(failedFtpJobs).replace('\x00', ''))

#            print("ftpJob \"" + command + "\" attempt " + str(count) + \
#                  " failed. Retrying.")

    return ftpJobDone, returnVal

def ftpQuit(ftp):
    """
    version required by: extracts
    """

    if type(ftp) == FTP:
        try:
            ftp.quit()
        except:
            pass


def ftpGetMd5(f, ftp):
    """
    code from http://smithje.github.io/python/2013/07/02/md5-over-ftp

    Fetches MD5 of specified file on FTP server.

    version required by: extracts
    """
    f_md5 = hashlib.md5()
    ftp.retrbinary('RETR {}'.format(f), f_md5.update)
    f_md5 = f_md5.hexdigest()
    return f_md5

def dashToSpace(chars):
    """
    Remove dash characters from chars.

    Dash characters have been collected from Wikipedia
    (https://en.wikipedia.org/wiki/Dash#Similar_Unicode_characters)

    version required by: both
    """
    return re.sub('\u2012|\u2013|\u2014|\u2015|\u2053|\u2E3A|\u2E3B|\u2012|\
                  \u2013|\u2014|\u2015|\u2053|\u007E|\u02DC|\u223C|\u301C|\
                  \uFF5E|\u002D|\u005F|\u007E|\u00AD|\u00AF|\u005F|\u203E|\
                  \u02C9|\u02CD|\u02D7|\u02DC|\u2010|\u2011|\u2012|\u203E|\
                  \u00AF|\u2043|\u207B|\u208B|\u2212|\u223C|\u23AF|\u23E4|\
                  \u2500|\u2796|\u2E3A|\u2E3B|\u10191|\u058A|\u05BE|\u1400|\
                  \u1428|\u1806|\u1B78|\u2E0F|\u2E17|\u2E1A|\u2E40|\u30A0|\
                  \u3161|\u1173|\u301C|\u3030|\u30FC|\u4E00|\uA4FE|\uFE31|\
                  \uFE32|\uFE58|\uFF5E|\uFE63|\uFF0D|\u10110|\u1104B|\u11052|\
                  \u110BE|\u1D360', ' ', chars)

def dbConExe(db, command, **kwargs):
    """
    Temporarily connect to db and return rows if available

    version required by: extracts
    """

    done = False
    while not done:
        try:
            with db.connect() as conn:
                if kwargs:
                    result = conn.execute(command, kwargs)
                else:
                    result = conn.execute(command)

                done = True

                if result.returns_rows:
                    return result.fetchall()
        except:
            pass

def getXmlIterTreeAndRoot(f):
    """
    f is a file object for XML.
    Creates an iterator object for XML, iterates until root element is found,
    then returns the iterator object (xmlIterTree) and root.

    Root element is acquired for memory management purpose. While iterating
    through xmlIterTree, root element will be cleared every time an element's
    end is reached. Otherwises memory usage keeps increasing
    (see http://effbot.org/zone/element-iterparse.htm).

    version required by: both
    """
    # This line is needed in xmlToDb function in "extracts" version.
    # This is because XML file is read twice. At second reading, this returns
    # the file position indicator (or "cursor", so-to-speak) to the beginning
    # of the XML.
    f.seek(os.SEEK_SET)

    xmlIterTree = ET.iterparse(f, events=('start', 'end'))

    # get XML's root element (for memory management)
    # (based on http://effbot.org/zone/element-iterparse.htm)
    for event, elem in xmlIterTree:
        if event == 'start':
            root = elem
            break

    return xmlIterTree, root


def updateDb(db):
    """
    Downloads XMLs from Pubmed's FTP server and add data to database with xmlToDb.

    There are four logs.

    1. xmls_toDbDone.txt: XML files which have been downloaded and whose key info
                    have been moved to database

    2. xmls_toDbFailed.txt: XML files which
                    failed to be downloaded (former) or failed to be transferred
                    to database (latter). Thesse contain dictionaries
                    (e.g. {Example.xml.gz: 3} means Example.xml.gz failed 3 times
                    (to be downloaded or to be transferred to database)

    3. xmls_Renamed.txt: XML files sharing same MD5s, but having different
                            filenames

    4. xmls_onlyLocal.txt: XML files whose *filenames* are found in xmls_toDbDone.txt,
                            but not in Pubmed FTP server. Record inlcuding the
                            filename is extracted from xmls_toDbDone.txt and added
                            here first, but removed afterwards if an XML file
                            sharing the same MD5 (with different filename,
                            obviously) is found in the Pubmed FTP server.


    Note 1 (regarding "xmls_onlyLocal.txt" and "xmls_Renamed.txt"):
        These files are for in case XML files are renamed in the Pubmed FTP server.
        I believe that such renaming could be an error, or part of annual update
        (e.g. perhaps the filename begging will be changed from "medline17n" to
        "medline18n" for the year 2018?).

    Note 2 (regarding variable names):
        Often if not always,
            "x" refers to XML's filename,
            "m" referst to XML's MD5 (digital fingerprint), and
            "xm" refers to XML's filename and MD5.

    Note 3:
        set is often used instead of list to ensure there are no repeating values.

    version required by: extracts
    """
#    print("db update started")
    global dbUpdating

    # file names
    loc_file = "logs_updateDb/xmls_onlyLocal.txt"
    x_rename_log_file = "logs_updateDb/xmls_Renamed.txt"
    log_file = "logs_updateDb/xmls_toDbDone.txt"
    toDbFail_file = "logs_updateDb/xmls_toDbFailed.txt"
    downSuccess_file = "logs_updateDb/xmlDownloadSuccess.txt"

    # for error logging
    errsToLogInOneLine = ["database is locked"]

    # 1. load records of downloaded XMLs and their MD5s
    with open(log_file, "a+") as f:
        f.seek(os.SEEK_SET)

        # x_log contains filenames only. xm_log contains filenames and MD5s
        xm_log = set(f.read().replace('\x00', '').splitlines())
        x_log = set([re.sub(".*\)= ", "", line) for line in xm_log])

    # 2. get list of xlm files in Pubmed FTP server
    ftpAddress = 'ftp.ncbi.nlm.nih.gov'
    directories = ['/pubmed/baseline', '/pubmed/updatefiles']

    for directory in directories:

        # get current directory
#        print("Getting current directory in FTP server")
        ftpJobDone, currentDir = ftpJob(ftpAddress, directory, "returnVal = ftp.pwd()")
#        print("Got current directory in FTP server")

        # get XML files on Pubmed FTP server
#        print("Fetching list of XML files on FTP server, " + currentDir + " directory")
        ftpJobDone, x_ftp = ftpJob(ftpAddress, directory, "returnVal = set(ftp.nlst('*.xml.gz'))")
#        print("Fetched list of XML files on FTP server, " + currentDir + " directory")

        # 2.5 check XML files in xmls_onlyLocal.txt if they share same filename
        # as those in Pubmed FTP server. If they share same MD5, remove from log.
        with open(loc_file, "a+") as f:
            f.seek(os.SEEK_SET)
            xmLoc = set(f.read().replace('\x00', '').splitlines())
            xLoc = set([re.sub(".*\)= ", "", rec) for rec in xmLoc])

#        print("Checking XML files existing both locally and on FPT server")
        x_localAndFtp = xLoc & x_ftp

        for xLf in x_localAndFtp:

            # get MD5 from Pubmed FTP server
#            print("Getting MD5 of " + xLf + " found both locally and FTP server")
            ftpJobDone, xLf_m_ftp = ftpJob(ftpAddress, directory, "returnVal = ftpGetMd5(xLf, ftp)")
#            print("Got MD5 of " + xLf)

            # get logged MD5
            for rec in xmLoc:
                if xLf in rec:
                    xmLf = re.sub("MD5\(|\)= .*", "", rec)

                    # if same MD5 is shared, remove XML from log
                    if xmLf == xLf_m_ftp:
                        xmLoc.remove(rec)
                        with open(loc_file, "w") as f:
                            for r in xmLoc:
                                f.write("{}\n".format(r).replace('\x00', ''))
                        break

        # 3. log xml files existing in local directory, but not in Pubmed ftp server
        # (judged by filenames instead of MD5s)
#        print("Checking XML files existing only locally")
        x_onlyLocal = x_log - x_ftp

        if x_onlyLocal:
            with open(loc_file, "w") as f:
                for xLoc in x_onlyLocal:
                    xmLoc = set([line for line in xm_log if xLoc in line])
                    for rec in xmLoc:
                        # the whole log is re-written. This way, xml files reappearing
                        # in the Pubmed ftp server is removed from the log.
                        f.write("{}\n".format(rec).replace('\x00', ''))

        # 4. download and log XML files existing only in Pubmed ftp server, but not locally

        # 4.1 find xml files existing in Pubmed FTP server, but not in local directory
        # (judged by filenames instead of MD5s)
#        print("Checking XML files existing only on FTP server")
        x_FilenameOnlyInFtp = sorted(x_ftp - x_log)

        index = -1
        for newX in x_FilenameOnlyInFtp:

            index += 1

            # 4.2 log and skip XML if XML on FTP is a renamed version of an
            # already downloaded-and-processed XML

            # extract MD5 from XML on Pubmed FTP server
            # code from http://smithje.github.io/python/2013/07/02/md5-over-ftp
#            print("Fetching MD5 from FTP server for " + newX)
            ftpJobDone, newM_ftp = ftpJob(ftpAddress, directory, "returnVal = ftpGetMd5('{}', ftp)".format(newX))
#            print("Fetched MD5 from FTP server for " + newX)
            newXm = "MD5(" + newM_ftp + ")= " + newX

            # identify already-processed XMLs which has been renamed on Pubmed
            # FTP server
            xRenamed = ""
            xmRenamed = ""
            xm_log_list = list(xm_log)

            for i in range(len(xm_log)):
                line = xm_log_list[i]
                # if MD5 of new XML file is already in xmls_toDbDone.txt
                if newM_ftp in line:
                    xRenamed = re.sub(".*\)= ", "", line)
#                    print(newX + " is a renamed version of Already-processed " + xRenamed)
                    xmRenamed = line
                    xRenamed_m_ftp = ""

                    # add the existing XML's filename to x_FilenameOnlyInFtp if
                    # (1) and (2) are true - each described below

                    # (1) the XML's filename is present in Pubmed FTP server, and
                    if xRenamed in x_ftp:

                        # extract MD5 from XML on Pubmed FTP server
                        # code from http://smithje.github.io/python/2013/07/02/md5-over-ftp

#                        print("Getting MD5 of " + xRenamed + " whose filename matches the\
#                              XML file previously processed, but is a different file\
#                              (assumingly due to renaming on FTP server")
                        ftpJobDone, xRenamed_m_ftp = ftpJob(ftpAddress, directory, "returnVal = ftpGetMd5(xRenamed, ftp)")
#                        print("Got MD5 of " + xRenamed)

                        # (2) the XML's MD5 is absent from xmls_toDbDone.txt
                        if xRenamed_m_ftp not in [l for l in xm_log]:
                            x_FilenameOnlyInFtp.insert(index + 1, xRenamed)

                    # remove old filename from xmls_onlyLocal.txt
                    with open(loc_file, "a+") as f:
                        f.seek(os.SEEK_SET)
                        xmLoc = set(f.read().replace('\x00', '').splitlines())
                        for rec in xmLoc:
                            if newM_ftp in rec:
                                xmLoc.remove(rec)
                                break

                    with open(loc_file, "w") as f:
                        for rec in xmLoc:
                            f.write("{}\n".format(rec).replace('\x00', ''))

                    # update filename in xmls_toDbDone.txt
                    xm_log_list[i] = newXm
                    with open(log_file, "w") as f:
                        for l in set(xm_log_list):
                            f.write("{}\n".format(l).replace('\x00', ''))

                    # load renamed-XMLs log
                    with open(x_rename_log_file, "a+") as f:
                        f.seek(os.SEEK_SET)
                        x_rename_log = f.read().replace('\x00', '').splitlines()

                    # log renamed XML (new entry)
                    if not any(newM_ftp in l for l in x_rename_log):
                        with open(x_rename_log_file, "a") as f:
                            f.write("{} --> {}\n".format(xmRenamed, newX).replace('\x00', ''))

                    # log renamed XML (update existing entry)
                    else:
                        for i in range(len(x_rename_log)):
                            # if row contains new XML's MD5 and
                            # and the row does not end with the new XML's filename
                            if (newM_ftp in x_rename_log[i]) and \
                                (newX != x_rename_log[i].split(" --> ")[-1]):
                                x_rename_log[i] += " --> " + newX
                                break

                        with open(x_rename_log_file, "w") as f:
                            # code from https://stackoverflow.com/a/899176
                            for l in set(x_rename_log):
                                f.write("{}\n".format(l).replace('\x00', ''))

                    # stop searching in xmls_toDbDone.txt
                    break

            # update xmls_toDbFailed.txt if XML filename has changed in Pubmed FTP server
            toDbFail = logToDic(toDbFail_file)

            for x in toDbFail:
                if (toDbFail[x][0] == newM_ftp) and (x != newX):
                    # code from https://stackoverflow.com/a/16475444/7194743
                    toDbFail[newX] = toDbFail.pop(x)

                    with open(toDbFail_file, "w") as f:
                        f.write(str(toDbFail).replace('\x00', ''))

                    # stop searching in xmls_toDbFailed.txt
                    break


            # if current XML is just a renamed version of an already processed one,
            # check next XML
            if xmRenamed:
#                print("Skip to next XML file (" + newX + " already processed, \
#                      but renamed in FTP server")
                continue

            # 4.3 otherwise, download XML
            newM_loc = ""

            downloadStatus = ""
            downloaded = False
            count = 0
            while not downloaded:
                count += 1
                try:
                    # download XML and get its MD5
#                    print("Trying to download " + newX)
                    urlretrieve('ftp://' + ftpAddress + currentDir + '/' + newX, xml_extracts_dir + newX)
#                    print("Getting MD5 of downloaded " + newX)
                    newM_loc = hashlib.md5(open(xml_extracts_dir + newX, "rb").read()).hexdigest()
                except:
                    pass

                # 4.4 if the MD5 extracted from the downloaded XML and the one on
                # Pubmed FTP server match, ...
                if glob(xml_extracts_dir + newX) and newM_ftp == newM_loc:
#                    print(newX + " downloaded correctly")
                    downloadStatus = "downloadSuccess"
                    downloaded = True

                    saveVarAsLog(downSuccess_file, newX, 1, increment=True)

                    # transfer key XML contents to database
                    try:
#                        print(newX + ": xmlToDb executing")
                        xmlToDb_success = xmlToDb(db, xml_extracts_dir + newX)
                    except:
                        xmlToDb_success = False

                        # log full error message on xmlToDb failure
                        open(tempLog, 'w').close()
                        logging.exception("xmls_toDbFailed:")

                    # remove XML (to save space)
                    os.remove(xml_extracts_dir + newX)
#                    print(newX + " removed")

                    # if xmlToDb succeeded, ...
                    if xmlToDb_success:
#                        print(newX + ": xmlToDb success")

                        # add XML to xmls_toDbDone.txt
                        with open(log_file, "a") as f:
                            f.write("{}\n".format(newXm).replace('\x00', ''))

                        # remove XMl from xmls_toDbFailed.txt
                        removeFromLog(toDbFail_file, newX)

                    # if xmlToDb failed, log the XML
                    else:
                        with open(tempLog, "r") as f:
                            err_full = f.read().replace('\x00', '').splitlines()
                            err_lastLine = err_full[-1]
                            # log short error message if error in errsToLogInOneLine
                            err_oneLine = [i for i in errsToLogInOneLine if i in err_lastLine]
                            if err_oneLine:
                                value = [newM_ftp, downloadStatus, err_oneLine]
                            # log full error message for other errors
                            else:
                                value = [newM_ftp, downloadStatus, err_full]

                        saveVarAsLog(toDbFail_file, newX, value)

                        errMessage = newX + ": xmlToDb failed, aborting update, fix problem and retry. Error details can be found at {}, {} and {}".format(tempLog, upDbFail_part1_file, upDbFail_part2_file)

                        print(errMessage)
                        with open(upDbFail_part1_file, "w") as f:
                            f.write(errMessage.replace('\x00', ''))

                        dbUpdating = "failed"

                        return dbUpdating

                # if XML download failed, log the XML
                else:
                    downloadStatus = "downloadFailed"

                    toDbFail = logToDic(toDbFail_file)

                    if newX in toDbFail:
                        toDbFail[newX][1] = downloadStatus
                        value = toDbFail[newX]
                        saveVarAsLog(toDbFail_file, newX, value)
                    else:
                        value = [newM_ftp, downloadStatus, ""]
                        saveVarAsLog(toDbFail_file, newX, value)

#                    print(newX + " download attempt " + str(count) + " failed. Retrying.")

    dbUpdating = False
#    print("db update finished")

    return dbUpdating

def xmlToDb(db, xml):
    """
    Transfer records from XML file to db.
    For each record, only a subset of data are transferred.
    This excludes records which are outdated (e.g. due to a corrected version
    of article has been made available later) or deleted, or are suplementary
    materials.

    There are three logs. "Articles" are indicated as PMIDs in the logs.

    deletedPmids.txt: Articles marked as deleted in Medline database. These articles
                contain <DeleteCitation> element in XML file.

    discardedPmids.txt: Articles which (1) have been retracted or replaced by
                    later-published version or (2) are supplementary materials.
                    Two XML elements are checked: <CommentsCorrections> (where
                    'RefType' is looked at) and <PublicationType>.
                    element.

    xmlToDbNotDone.txt: Articles which have not been added to db due to
                        (1) essential info missing ("missingEssentialInfo") or
                        (2) no clear reason

                        The case of essential info missing is explained below.

                        Articles which have not been added to database due to key
                        info missing).

                        Potentially missing essential info includes
                        the following: fname and lname (author's first and
                        last names), pyear (publication year),
                        journal (journal title), and crYmd (Medline record
                        creation date).

                        xml (XML filename) and pmid are also
                        essential info, but they cannot have been missed if the
                        logging stage has been reached.

    version required by: extracts
    """
    # file and directory paths
    dePmids_file = "logs_xmlToDb/deletedPmids.txt"
    dPmids_file = "logs_xmlToDb/discardedPmids.txt"
    toDbNo_file = "logs_xmlToDb/xmlToDbNotDone.txt"

    # variables for handling articles to discard
    # ("rt" refers to "RefType", and "pt" refers to "PublicationType")
    rt_discardOld = {"ErratumIn", "PartialRetractionIn", "ReprintOf", \
                  "RepublishedFrom", "SummaryForPatientsIn"}

    rt_discardCurrent = {"ErratumFor", "PartialRetractionOf", "ReprintIn", \
                    "RepublishedIn", "OriginalReportIn", "RetractionIn", \
                    "RetractionOf"}

    pt_discardCurrent = {"Retracted Publication",  "Retraction of Publication", \
                         "Published Erratum"}

    # load records of articles to discard
    # (articles retracted or replaced by later-published version)
    dPmids = logToDic(dPmids_file)

    if dPmids == {}:
        dPmids["RefType"] = {}
        dPmids["PublicationType"] = {}

        # RefType to discard
        for d_rt in rt_discardCurrent:
            dPmids["RefType"][d_rt] = []

        # PublicationType to discard
        for d_pt in pt_discardCurrent:
            dPmids["PublicationType"][d_pt] = []

    d_rts = dPmids["RefType"]
    d_pts = dPmids["PublicationType"]

    d_rts_eFor = d_rts["ErratumFor"]
    d_rts_prOf = d_rts["PartialRetractionOf"]
    d_rts_reprIn = d_rts["ReprintIn"]
    d_rts_repubIn = d_rts["RepublishedIn"]
    d_rts_orIn = d_rts["OriginalReportIn"]

    # load records of articles with missing info (therefore not added to database)
    toDbNo = logToDic(toDbNo_file)

    if toDbNo == {}:
        toDbNo = {'missingEssentialInfo': {}, 'unknownProblem': set()}

    mDic = toDbNo['missingEssentialInfo']

    mPmids = getListsInDic(mDic)
    uPmids = toDbNo['unknownProblem']

    # load records of articles deleted from MEDLINE database
    # (code from https://stackoverflow.com/a/2967249 --> Nick Zalutskiy's comment.
    # This opens file to read, or creates it if it does not exist.)
    with open(dePmids_file, "a+") as f:
        f.seek(os.SEEK_SET)
        dePmids = set(f.read().replace('\x00', '').splitlines())

    with gzip.open(xml, 'r') as f:

        # read in XMl and get root
        xmlIterTree, root = getXmlIterTreeAndRoot(f)

        # 0. get list of articles deleted from MEDLINE database
        for event, elem in xmlIterTree:
            delCit = set()
            if event == 'end':
                if elem.tag == "DeleteCitation":
                    delCit = delCit.union(set([i.text for i in elem.findall('PMID')]))
                    # clear element to free memory
                    elem.clear()
                # clear root to free memory
                root.clear()

        # 0.1 log deleted articles
        if delCit != set():
            with open(dePmids_file, "a") as f:
                for dePmid in delCit:
                    if dePmid not in dePmids:
                        dePmids.add(dePmid)
                        f.write("{}\n".format(dePmid).replace('\x00', ''))

        # 0.2 remove deleted articles from database
        for dePmid in dePmids:
            dbConExe(db, "DELETE FROM medline WHERE pmid=:dePmid", dePmid=dePmid)

        # check each article
        pmids_NotProcessed = set()

        # read in XMl and get root again
        xmlIterTree, root = getXmlIterTreeAndRoot(f)

        for event, elem in xmlIterTree:
            if event == 'end':
                if elem.tag == "MedlineCitation":

                    # 1. get PMID and elements of interest from XML
                    # 1.1 get PMID (unique identifier for article) and other main info
                    pmid = None
                    pmid = elem.find('PMID').text
                    pmids_NotProcessed.add(pmid)
#                    print("processing pmid " + pmid)

                    # 1.2 get XML elements for essential info
                    authorList = elem.findall('.//AuthorList/Author[@ValidYN="Y"][LastName][ForeName]')
                    pYmdList = elem.findall('.//Article/Journal/JournalIssue/PubDate')
                    journalList = elem.findall('MedlineJournalInfo/MedlineTA')
                    crYmdList = elem.findall('DateCreated')

                    # 1.3 get XML elements for extra info
                    journalOtherInfoList = elem.findall('.//Article/Journal')
                    articleList = elem.findall('.//Article/ArticleTitle')
                    doiList = elem.findall('.//Article/ELocationID[@EIdType="doi"][@ValidYN="Y"]')
                    countryList = elem.findall('.//MedlineJournalInfo/Country')
                    coYmdList = elem.findall('DateCompleted')
                    reYmdList = elem.findall('DateRevised')

                    pageNum = None
                    try:
                        pageNum = elem.find('.//Article/Pagination/MedlinePgn').text
                    except:
                        pass

                    # 2. handle articles to discard

                    # 2.1 as indicated in relevent XML elements
                    cc_list = elem.findall('.//CommentsCorrectionsList/CommentsCorrections')
                    pt_list = elem.findall('.//PublicationTypeList/PublicationType')

#                    print("checking CommentsCorrections")
                    # check "CommentsCorrections" element
                    for cc in cc_list:
                        rt = cc.get("RefType")
                        dPmid = None

                        # 2.1.1 Current article is fine. But, a related article
                        # should be excluded if it is (1) an old version replaced
                        # by current version ("ReprintOf", "RepublishedFrom"),
                        # (2) supplementary material for current article
                        # ("SummaryForPatientsIn")), or (3) notification of
                        # correction for current article ("ErratumIn",
                        # "PartialRetractionIn").

                        if rt in rt_discardOld:
                            try:
                                dPmid = cc.find("PMID").text
                            except:
                                pass

                        # 2.1.2 Current article should be discarded if it has
                        # been retracted ("RetractionIn"), or is a retraction
                        # notification for another article ("RetractionOf"),
                        # notification of correction ("ErratumFor",
                        # "PartialRetractionOf"), an old version replaced by
                        # a later version ("ReprintIn", "RepublishedIn") or
                        # supplementary material ("OriginalReportIn")

                        elif rt in rt_discardCurrent:
                            dPmid = pmid

                        # note details of discarded version
                        if dPmid:
                            if rt in rt_discardOld:
                                if (rt == "ErratumIn") and (dPmid not in d_rts_eFor):
                                    d_rts_eFor.append(dPmid)
                                elif (rt == "PartialRetractionIn") and (dPmid not in d_rts_prOf):
                                    d_rts_prOf.append(dPmid)
                                elif (rt == "ReprintOf") and (dPmid not in d_rts_reprIn):
                                    d_rts_reprIn.append(dPmid)
                                elif (rt == "RepublishedFrom") and (dPmid not in d_rts_repubIn):
                                    d_rts_repubIn.append(dPmid)
                                elif (rt == "SummaryForPatientsIn") and (dPmid not in d_rts_orIn):
                                    d_rts_orIn.append(dPmid)
                            elif (rt in rt_discardCurrent) and (dPmid not in d_rts[rt]):
                                d_rts[rt].append(dPmid)

#                    print("checking PublicationType")
                    # check "PublicationType" element
                    # same as step "2.1.2" (see above)
                    for ptElement in pt_list:
                        pt = ptElement.text
                        dPmid = None

                        if pt in pt_discardCurrent:
                            dPmid = pmid

                        # note details of discarded version
                        if dPmid and (dPmid not in d_pts[pt]):
                            dPmid = pmid
                            d_pts[pt].append(dPmid)

                    # log discarded articles
                    if dPmids:
#                        print("logging discarded articles")
                        with open(dPmids_file, "w") as f:
                            f.write("{}\n".format(str(dPmids)).replace('\x00', ''))

                    # remove discarded articles from database
                    for dPmid in dPmids:
#                        print("removing discarded articles from db")
                        dbConExe(db, "DELETE FROM medline WHERE pmid=:dPmid", dPmid=dPmid)

                    pmids_NotProcessed = pmids_NotProcessed - set([i for i in dPmids])

                    # 2.2 as indicated by missing essential info

                    record_dates = crYmdList + coYmdList + reYmdList # required to get fiYmd
                    essential = {"AuthorList": authorList, "PubDate": pYmdList, \
                               "MedlineTA": journalList, "record_dates": record_dates}

                    missing_elements = set([i for i in essential if not essential[i]])
#                    print("checking for missing elements")
                    if missing_elements:
#                        print("missing elements found and being dealt with")

                        if pmid not in mPmids:
                            mPmids.append(pmid)

                        for me in missing_elements:

                            if me not in mDic:
                                mDic[me] = [pmid]
                            else:
                                mDic[me].append(pmid)

                        # this line is included as a precaution, but it may not be necessary
                        toDbNo['missingEssentialInfo'] = mDic

                        # update log
                        with open(toDbNo_file, "w") as f:
                            f.write(str(toDbNo).replace('\x00', ''))

                        try:
                            pmids_NotProcessed.remove(pmid)
                        # catch error in case article was already 'deleted' or 'discarded'
                        except:
                            pass

                    # skip current article if it has been deleted, discarded or
                    # is missing essential info
                    if (pmid in dePmids) or (pmid in dPmids) or (pmid in mPmids):
#                        print("skipping pmid " + pmid + " due to 'deleted', 'discarded' or missing essential info")
                        continue

                    # 4. transfer info from XML to db
                    # 4.1 collect info
#                    print("extracting info from pmid " + pmid)
                    # author and initials
                    lname = []
                    fname = []
                    initials = []

                    for author in authorList:
                        lname.append(toASCII(dashToSpace(author.find("LastName").text)))
                        fname.append(toASCII(dashToSpace(author.find("ForeName").text)))
                        try:
                            initials.append(toASCII(dashToSpace(' '.join([i + '.' for i in author.find("Initials").text]))))
                        except:
                            initials.append(toASCII(dashToSpace(' '.join([i[0] + '.' for i in fname.split()]))))

                    lname = '___'.join(lname) # assuming no author has "___" in their names
                    fname = '___'.join(fname)
                    initials = '___'.join(initials)

                    # publication year, month, date
                    pyear = None
                    pmonth = None
                    pday = None
                    for pYmd in pYmdList:
                        try:
                            pyear = pYmd.find("Year").text
                            pmonth = datetime.datetime.strptime(pYmd.find("Month").text, "%b").strftime("%m")
                            pday = (pYmd.find("Day").text).zfill(2)
                        except:
                            if pyear == None:
                                try:
                                    medlineDate = pYmd.find("MedlineDate").text
                                    try:
                                        pyear = str(int(medlineDate[:4]))

                                    # extract 4-digit number (code from https://stackoverflow.com/a/4289557)
                                    except:
                                        pyear = str([int(s) for s in medlineDate.split() if s.isdigit() and len(s) == 4][-1])
                                except:
                                    pass

                    # journal title
                    journal = None
                    for journal in journalList:
                        journal = toASCII(dashToSpace(journal.text))

                    # article title
                    article = None
                    for article in articleList:
                        article = article.text

                    # other journal info 1
                    journalIss = None

                    for jInfo in journalOtherInfoList:

                        # journal title (non-abbreviated)
                        journalNonAbbr = None
                        try:
                            journalNonAbbr = toASCII(dashToSpace(jInfo.find('Title').text))
                        except:
                            journalNonAbbr = journal


                        for ji in jInfo.findall('JournalIssue'):
                            journalVol = None
                            # journal volume
                            try:
                                journalVol = ji.find('Volume').text
                            except:
                                pass

                            # journal issue
                            journalIss = None
                            try:
                                journalIss = ji.find('Issue').text
                            except:
                                pass

                    # doi number
                    doi = None
                    for doi in doiList:
                        doi = doi.text

                    # country where journal was published
                    country = None
                    for country in countryList:
                        country = country.text

                    # note MEDLINE record dates (year, month, date) - created, completed and revised
                    # note most recent date as "fiYmd"
                    fiYmd = None

                    # created (oldest date among three)
                    crYmd = None
                    for crYmd in crYmdList:
                        crYmd = crYmd.find("Year").text + \
                                (crYmd.find("Month").text).zfill(2) + \
                                (crYmd.find("Day").text).zfill(2)
                        fiYmd = crYmd

                    # completed
                    coYmd = None
                    for coYmd in coYmdList:
                        coYmd = coYmd.find("Year").text + \
                                (coYmd.find("Month").text).zfill(2) + \
                                (coYmd.find("Day").text).zfill(2)
                        fiYmd = coYmd

                    # revised (most recent)
                    reYmd = None
                    for reYmd in reYmdList:
                        reYmd = reYmd.find("Year").text + \
                                (reYmd.find("Month").text).zfill(2) + \
                                (reYmd.find("Day").text).zfill(2)
                        fiYmd = reYmd

                    # 4.2 skip current article if *full* record is already in db
                    toInsert = (pmid, fiYmd, reYmd, coYmd, crYmd, fname, \
                                lname, initials, pyear, pmonth, pday, journal, \
                                journalNonAbbr, article, journalVol, journalIss, \
                                pageNum, doi, country)

#                    print("check if pmid " + pmid + " is in db")
                    eRec = dbConExe(db, "SELECT * FROM medline WHERE pmid=:pmid", pmid=pmid)

                    if eRec:
                        eRec = eRec[0]

                        existingRecord = (str(eRec['pmid']), eRec['fiYmd'], \
                                eRec['reYmd'], eRec['coYmd'], eRec['crYmd'], \
                                eRec['fname'], eRec['lname'], eRec['initials'], \
                                eRec['pyear'], eRec['pmonth'], eRec['pday'], \
                                eRec['journal'], eRec['journalNonAbbr'], \
                                eRec['article'], eRec['journalVol'], \
                                eRec['journalIss'], eRec['pageNum'], \
                                eRec['doi'], eRec['country'])

                        if toInsert == existingRecord:
                            pmids_NotProcessed.remove(pmid)
#                            print("pmid " + pmid + "'s full record already in db, skipping to next pmid")
                            continue

                    # 4.3 otherwise, check if article record exists in db at all
                    #
                    # db might contain ...
                    # (1) full record of a *different* version or
                    # (2) partial record of the same version
                    #
                    # Case (2), although very unlikely to occur, refers to
                    # when records are written only partially. This can be
                    # due to, for example, power failure. SQLite will automatically
                    # "roll back" these partially written records as long as
                    # the journal file is not deleted (see first paragraph and
                    # section "1.3" at https://www.sqlite.org/howtocorrupt.html).
                    # This means that any record existing in db will very likely
                    # be full. However, to be safe, I will replace any db record
                    # with the current one if they share the same *pmid* and *fiYmd*.

                    pmid_exists_in_db = [i for i in dbConExe(db, "SELECT EXISTS(SELECT * FROM medline WHERE pmid=:pmid LIMIT 1)", pmid=pmid)][0][0]

                    insertionDone = False

                    # if db record exists for article
                    if pmid_exists_in_db:
#                        print("pmid " + pmid + " already in db. ", end="")

                        # note most recent date of db record
                        fiYmd_db = [i for i in dbConExe(db, "SELECT fiYmd FROM medline WHERE pmid=:pmid", pmid=pmid)][0][0]

                        # if current record is up-to-date (as new as or newer than
                        # db record), update (replace) db record with current record
                        currentRecordIsUpToDate = int(fiYmd) >= int(fiYmd_db)

                        if currentRecordIsUpToDate:
#                            print("But, db is outdated. Inserting current record into db")
                            dbConExe(db, "INSERT OR REPLACE INTO medline (pmid, \
                                            fiYmd, reYmd, coYmd, crYmd, fname, \
                                            lname, initials, pyear, pmonth, pday, \
                                            journal, journalNonAbbr, article, \
                                            journalVol, journalIss, pageNum, \
                                            doi, country) \
                                        VALUES (:pmid, :fiYmd, :reYmd, :coYmd, :crYmd, \
                                                :fname, :lname, :initials, :pyear, :pmonth, \
                                                :pday, :journal, :journalNonAbbr, :article, \
                                                :journalVol, :journalIss, :pageNum, :doi, \
                                                :country)", \
                                                pmid=pmid, fiYmd=fiYmd, reYmd=reYmd, \
                                                coYmd=coYmd, crYmd=crYmd, \
                                                fname=fname, lname=lname, \
                                                initials=initials, \
                                                pyear=pyear, pmonth=pmonth, \
                                                pday=pday, journal=journal, \
                                                journalNonAbbr=journalNonAbbr, \
                                                article=article, \
                                                journalVol=journalVol, \
                                                journalIss=journalIss, \
                                                pageNum=pageNum, doi=doi, \
                                                country=country)
                            insertionDone = True

                        # if current record is outdated, abandon it
                        else:
                            pmids_NotProcessed.remove(pmid)
#                            print("db is up-to-date. Not inserting current record into db, skipping to next pmid")
                            continue

                    # if article does not exist in db, add record to db
                    else:
#                        print("pmid " + pmid + " not already in db. Inserting current record into db")
                        dbConExe(db, "INSERT INTO medline (pmid, \
                                            fiYmd, reYmd, coYmd, crYmd, fname, \
                                            lname, initials, pyear, pmonth, pday, \
                                            journal, journalNonAbbr, article, \
                                            journalVol, journalIss, pageNum, \
                                            doi, country) \
                                        VALUES (:pmid, :fiYmd, :reYmd, :coYmd, :crYmd, \
                                                :fname, :lname, :initials, :pyear, :pmonth, \
                                                :pday, :journal, :journalNonAbbr, :article, \
                                                :journalVol, :journalIss, :pageNum, :doi, \
                                                :country)", \
                                                pmid=pmid, fiYmd=fiYmd, reYmd=reYmd, \
                                                coYmd=coYmd, crYmd=crYmd, \
                                                fname=fname, lname=lname, \
                                                initials=initials, \
                                                pyear=pyear, pmonth=pmonth, \
                                                pday=pday, journal=journal, \
                                                journalNonAbbr=journalNonAbbr, \
                                                article=article, \
                                                journalVol=journalVol, \
                                                journalIss=journalIss, \
                                                pageNum=pageNum, doi=doi, \
                                                country=country)
                        insertionDone = True

                    # check if insertion was successful
                    ins = dbConExe(db, "SELECT * FROM medline WHERE pmid=:pmid", pmid=pmid)
                    if ins:
                        ins = ins[0]

                        inserted = (str(ins['pmid']), ins['fiYmd'], \
                                ins['reYmd'], ins['coYmd'], ins['crYmd'], \
                                ins['fname'], ins['lname'], ins['initials'], \
                                ins['pyear'], ins['pmonth'], ins['pday'], \
                                ins['journal'], ins['journalNonAbbr'], \
                                ins['article'], ins['journalVol'], \
                                ins['journalIss'], ins['pageNum'], \
                                ins['doi'], ins['country'])

                        if insertionDone and toInsert == inserted:
#                            print("insertion success")
                            pmids_NotProcessed.remove(pmid)
                    # debugging purpose
                    else:
#                        print("xmlToDb failed for " + pmid + " in " + xml)
                        pass

                    # clear element to free memory
                    elem.clear()
                # clear root to free memory
                root.clear()

    # 4.4.2 log if any article has not been transferred
    if pmids_NotProcessed:
#        print("Logging pmids not inserted to db for unknown reasons")
        uPmids = uPmids.union(pmids_NotProcessed)
        toDbNo['unknownProblem'] = uPmids

        # update log
        with open(toDbNo_file, "w") as f:
            f.write(str(toDbNo).replace('\x00', ''))

    # indicate if function finished successfully
    return True

def saveVarAsLog(logName, key, value, increment=False):
    """
    Creates and or update a dictionary with "key" and "value",
    then saves the dicitonary into a log ("logName").

    version required by: extracts
    """

    with open(logName, "a+") as f:
        f.seek(os.SEEK_SET)
        log = f.read().replace('\x00', '')

    # update log
    if log:
        try:
            log = ast.literal_eval(log)
        except:
            log = eval(log)
        
        if increment and (key in log):
            log[key] += 1
        else:
            log[key] = value

    # or create log
    else:
        log = {key: value}

    # write to file
    with open(logName, "w") as f:
        f.write(str(log).replace('\x00', ''))

def logToDic(logName):
    """
    "logName" is a log with dict saved as string.
    Returns dict converted from the string.

    version required by: extracts
    """
    with open(logName, "a+") as f:
        f.seek(os.SEEK_SET)

        # in case a file is filled with '\x00' (null bytes)
        # code based on https://stackoverflow.com/a/4169762/7194743
        dicStr = f.read().replace('\x00', '')

        if not dicStr:
            dicStr = '{}'

        try:
            dic = ast.literal_eval(dicStr)
        except:
            dic = eval(dicStr)

    return dic

def getListsInDic(dic):
    """
    dic is a dictionary whose values are lists.
    Combines and returns all lists in dic.

    version required by: extracts
    """
    out = []

    for lst in dic:
        for i in lst:
            if i not in out:
                out.append(dic[lst])

    return out


def updateDbStart(db):
    """
    This function runs every "interval" seconds.

    "updateDb" function begins if dbUpdating is True.
    Nothing is done if dbUpdating is False.
    "updateDb" function stops running if dbUpdating is "failed"

    dbUpdating should be initially set to False from outside the function.
    Then, it's repeatedly updated within function by return value of
    "updateDb" function.

    version required by: extracts
    """
    global dbUpdating

    interval = 600
    if dbUpdating == "failed":
        # failure message is printed to the console by xmlToDb function
        return
    elif dbUpdating == True:
        pass
    elif dbUpdating == False:
        dbUpdating = True
        try:
            dbUpdating = updateDb(db)
        except:
            open(tempLog, 'w').close()
            logging.exception("updateDb failed:")

            with open(tempLog, "r") as f:
                err_full = f.read().replace('\x00', '').splitlines()

            with open(upDbFail_part2_file, "w") as f:
                for line in err_full:
                    f.write("{}\n".format(line).replace('\x00', ''))

            return

    time.sleep(interval)
    updateDbStart(db)

def sortRefs(ref):
    '''
    Sort reference info unaffected by '&', ' ' and ','.

    Code based on https://stackoverflow.com/ref/5212885/7194743
    Alternative method at https://stackoverflow.com/a/4233482/7194743

    version required by: both
    '''

    indices = []
    for i in range(len(ref[0])):
        indices.append(i)

    ref_stripped = []
    for i in range(len(ref)):
        ref_stripped.append([re.sub("&| |,", "", j) for j in ref[i]])
        ref_stripped[i].append(i)

    ref_stripped_sorted = sorted(ref_stripped, key=itemgetter(*indices))

    ref_sorted = []
    for i in range(len(ref_stripped_sorted)):
        ind = ref_stripped_sorted[i][-1]
        ref_sorted.append(ref[ind])

    return ref_sorted

def generateXmlFilename(size=8, chars=string.ascii_letters + string.digits, filepath=xml_original_dir):
    """
    Generate an XML filename with 8-digit strings. The strings are 
    a combination of randomly chosen lowercase aplphabet letters ([a-z]) and
    numbers ([0-9]). This function makes sure that a new filename is different
    from an existing one.

    This is done to prevent one XML overwriting another in case multiple XML
    downloads are invoked at the same time (e.g. if several users submit queries
    at similar times).

    version required by: original
    """
    notDone = True

    while notDone:
        # code from https://stackoverflow.com/a/2257449/7194743
        xml = filepath + ''.join(random.choice(chars) for _ in range(size)) + ".xml"
        notDone = glob(xml)

    return xml

def mergeSimilarSpelledAuthors(records):
    """
    Merge two author records if their names are spelled the same way, but in
    different letter cases (e.g. Mike vs mike).
    
    version required by: both
    """
    
    def mergeJournalsYears(ind, key):
        """
        Merge "journals" and "years" of records.
        
        Variable names:
        "k": to keep (e.g. "auK": author spelling to keep)
        "r": to remove (e.g. auR": author spelling to discard
                        (after adding its record to "auK"))
        "i": item (e.g. "i" in "Journals" is a journal name)
        "rec": records for the item
        
        """
        auK_iRec = records[auK][ind][key]
        auK_i = set([i for i in auK_iRec])
        
        auR_iRec = records[auR][ind][key]
        auR_i = set([i for i in auR_iRec])

        for ik in auK_i:
            for ir in auR_i:
                
                ikRec = auK_iRec[ik]
                irRec = auR_iRec[ir]
                
                if ik != ir:
                    auK_iRec[ir] = irRec
                else:
                    auK_iRec[ik] = sumLists(ikRec, irRec)

    def sumLists(l1, l2):
        return [ l1 + l2 for l1, l2 in zip(l1, l2) ]
    
    # list of all authors
    auAll = set([k for k in records])
    
    # authors to remove
    toRemove = set()
    
    # iterate over authors
    for au1 in records:
        for au2 in auAll:
            au1lo = au1.lower()
            au2lo = au2.lower()
            
            # if two authors' names are spelled the same, but in different cases
            if au1 != au2 and au1lo == au2lo:

                au1_t = records[au1][0]["total"]
                au2_t = records[au2][0]["total"]
                
                # keep the name with more records
                auK, auR = (au1, au2) if au1_t >= au2_t else (au2, au1)

                # get records
                auR_t = records[auR][0]["total"]

                # merge authors
                records[auK][0]["total"] += auR_t
                mergeJournalsYears(1, "journals")
                mergeJournalsYears(2, "years")
                            
                toRemove.add(auR)
                    
                # merge "journals"

            
        auAll.remove(au1)
             
    for e in toRemove:
        records.pop(e)
    
    return records

def sortRefInfo(records):
    """
    Sort reference info for "journals" and "years" in records
    
    version required by: both
    """
    
    def sortRefInfoJournalsYears(author, ind, key):
        """
        Sort reference info for "journals" and "years" in records
        
        version required by: both
        """

        for i in records[author][ind][key]:
            iRec = records[author][ind][key][i]
            iRec[1] = sortRefs(iRec[1])
    
    for author in records:
        sortRefInfoJournalsYears(author, 1, "journals")
        sortRefInfoJournalsYears(author, 2, "years")
    
    return records

'''
This is a different version of toASCII, discarded due to slow performance.
This version can save some extended ASCII symbols (e.g. ""). These symbols are
omitted by unidecode, but saved by unicodedata.


def toASCII(s):
    """
    Converts extended-ASCII character to regular ASCIIi character
    (e.g. ä --> a)

    Codes are based on those at following pages
    https://stackoverflow.com/a/2633310
    https://stackoverflow.com/a/518232

    version required by: both
    """

    # if all chracters are regular ASCII, return original string
    if all(ord(c) < 128 for c in s):
        return s

    # otherwise, decode with unidecode
    sList = list(s)
    dList = []

    for i in range(len(sList)):
        unidec = unidecode(sList[i])
        if unidec != '':
            dList.append(unidec)

    # if any character is omitted, decode with unicodedata
        else:
            for dec in unicodedata.normalize('NFD', sList[i]):
                if unicodedata.category(dec) != 'Mn':
                    dList.append(dec)

    d = ''.join(dList)

    return d
'''

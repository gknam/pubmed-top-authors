import datetime
import re
import sys
import collections
import unicodedata
from unidecode import unidecode
import urllib, json
import xml.etree.ElementTree as ET

def getXmlIterTreeAndRoot(f):
    """
    f is a file object for XML.
    Creates an iterator object for XML, iterates until root element is found,
    then returns the iterator object (xmlIterTree) and root.

    Root element is acquired for memory management purpose. While iterating
    through xmlIterTree, root element will be cleared every time an element's
    end is reached. Otherwises memory usage keeps increasing
    (see http://effbot.org/zone/element-iterparse.htm).
    """
    xmlIterTree = ET.iterparse(f, events=('start', 'end'))

    # get XML's root element (for memory management)
    # (based on http://effbot.org/zone/element-iterparse.htm)
    for event, elem in xmlIterTree:
        if event == 'start':
            root = elem
            break

    return xmlIterTree, root

def getPmids(term, retmax, reldate):
    """Get PMIDs for term."""
    
    retmax = round(int(retmax))
    reldate = round(int(reldate))
    
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
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={}&retmax={}&retstart={}&reldate={}&datetype=pdat&sort=pub+date".format(urllib.parse.quote(term), urllib.parse.quote(str(retmax_part)), urllib.parse.quote(str(retstart)), urllib.parse.quote(str(reldate)))
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

    # return results
    return pmids

def getFullRecs(pmids):
    """ Get full records from PMID """

    # info for a summary report to be given in the front-end.
    # pmids_included: number of articles checked (after excluding inappropriate ones)
    # pubYear_oldest: publication year for oldest article fetched.
    
    pmids_included = len(pmids)
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

    xml = "/home/gknam/Desktop/pubmed.xml"
    open(xml, "w").close()

    # get records from Pubmed
    # note: To minimise use of memory, the requested XML will be saved as file
    # and each element will be accessed iteratively (instead of directly
    # loading the whole XML into memory)

    # 1. using GET method
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&retmode=xml".format(pmids)
        urllib.request.urlretrieve(url, filename=xml)
    # 2. using POST method (if pmids is too long)
    except urllib.error.HTTPError:
        ids = urllib.parse.urlencode({"id": pmids}).encode("utf-8")
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml"
        urllib.request.urlretrieve(url, filename=xml, data=ids)

    # for checking articles to exclude
    rt_discardCurrent = {"ErratumFor", "PartialRetractionOf", "ReprintIn", \
                    "RepublishedIn", "OriginalReportIn", "RetractionIn", \
                    "RetractionOf"}

    pt_discardCurrent = {"Retracted Publication",  "Retraction of Publication", \
                         "Published Erratum"}

    with open(xml, "r") as f:
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
                        pmids_included -= 1
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
                            
                            lname = toASCII(au.find("LastName").text)
                            fname = toASCII(au.find("ForeName").text)
                            author = lname + ', ' + fname
                            record[0].append(author)

                            # this is extra info (i.e. not essential)
                            try:
                                initials = toASCII(' '.join([i + '.' for i in au.find("Initials").text]))
                            except:
                                initials = toASCII(' '.join([i[0] + '.' for i in fname.split()]))
                            
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
                                journal = toASCII(jAbbr.text)
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
                            aTitle = toASCII(a.find('ArticleTitle').text)
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
                                journalNonAbbr = toASCII(j.find('Title').text)
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
    
    # sort reference info
    for author in records:
        # sort ref for journals by year, then authors
        # (code from https://stackoverflow.com/a/4233482/7194743)
        for j in records[author][1]["journals"]:
            jRec = records[author][1]["journals"][j]
            refSorted = sorted(jRec[1], key = lambda x: (x[1], x[0]))
            jRec[1] = refSorted
        # sort ref for years by year, then authors
        for y in records[author][2]["years"]:
            yRec = records[author][2]["years"][y]
            refSorted = sorted(yRec[1], key = lambda x: (x[1], x[0]))
            yRec[1] = refSorted

    records = collections.OrderedDict(sorted(records.items()))

    return records, pmids_included, pubYear_oldest

def topAuthorsRecs(records, pmids_included, pubYear_oldest, numTopAuthors):
    """ get records of authors with most publication """

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
    topAuthorsRecs.update({"numberOfArticlesFetched": pmids_included})
    topAuthorsRecs.update({"oldestPubyearChecked": pubYear_oldest})

    return topAuthorsRecs


def toASCII(s):
    """
    Converts extended-ASCII character to regular ASCIIi character
    (e.g. ä --> a)

    Codes are based on those at following pages
    https://stackoverflow.com/a/2633310
    https://stackoverflow.com/a/518232
    """

    # if all chracters are regular ASCII, return original string
    if all(ord(c) < 128 for c in s):
        return s

    # otherwise, decode with unidecode
    d = unidecode(s)

    return d


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
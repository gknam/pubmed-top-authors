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

def getPmids(term):
    """Get PMIDs for term."""

    # maximum number of articles to retrieve
    retmax_limit = 100000
    retmax = 500000
    
    # subset of articles to start from
    # (e.g. if retstart is 0, articles are fetched from the beginning of the stack.
    # if retstart is 10, first 10 articles in the stack are ignored.
    retstart = 0
    
    # number of articles to fetch
    # https://www.grc.nasa.gov/www/k-12/Numbers/Math/Mathematical_Thinking/calendar_calculations.htm
    oneYear = 365.2422
    # number of days from now
    reldate = round(oneYear * 5)

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
    
    # get records from Pubmed
    record = [[], [], []]
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
    
    with open(xml, "r") as f:
        # read in XMl and get root
        xmlIterTree, root = getXmlIterTreeAndRoot(f)
    
        # note key info for each article
        for event, elem in xmlIterTree:
            if event == 'end':
                if elem.tag == "MedlineCitation":
                    # reset record
                    record = [[], [], []]                    

                    # ↓↓↓ check if article should be excluded: begin ↓↓↓ #
                    rt_discardCurrent = {"ErratumFor", "PartialRetractionOf", "ReprintIn", \
                                    "RepublishedIn", "OriginalReportIn", "RetractionIn", \
                                    "RetractionOf"}

                    pt_discardCurrent = {"Retracted Publication",  "Retraction of Publication", \
                                         "Published Erratum"}
                    
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
                        continue

                    # ↑↑↑ check if article should be excluded: end ↑↑↑ #
                    
                    # note author
                    try:
                        for author in elem.findall('.//AuthorList/Author[@ValidYN="Y"][LastName][ForeName]'): # 
                            author = toASCII(author.find("LastName").text + ', ' + author.find("ForeName").text)
                            type(author) # will crash if if <AuthorList> is missing (which is true for anonymous articles)
                            record[0].append(author)
                    except:
                        continue

                    # note publication year
                    for year in elem.findall('.//Article/Journal/JournalIssue/PubDate'):
                        try:
                            year = year.find("Year").text
                        except:
                            medlineDate = year.find("MedlineDate").text
                            try:
                                year = str(int(medlineDate[:4]))
                            # extract 4-digit number (code from https://stackoverflow.com/a/4289557)
                            except:
                                try:
                                    year = str([int(s) for s in medlineDate.split() if s.isdigit() and len(s) == 4][0])
                                except:
                                    continue
                            
                        record[1].append(year)
                            
                    # note journal title
                    for journal in elem.findall('MedlineJournalInfo/MedlineTA'):
                        
                        try:
                            journal = toASCII(journal.text)
                        except:
                            continue
                        
                        record[2].append(journal)
                
                    # add key info to records
                    # make sure there is no empty field
                    if [] not in record:
                        # add record to records
                        for author in record[0]:
                            
                            # author
                            if author not in records:
                                records[author] = [{"total": 1}, {"journals": {}}, {"years": {}}]
                            else:
                                records[author][0]["total"] += 1
                            
                            # journal title (code from http://stackoverflow.com/a/14790997)
                            if not any(journal == d for d in records[author][1]["journals"]):
                                records[author][1]["journals"][journal] = 1
                            else:
                                records[author][1]["journals"][journal] += 1
                
                            # publication year (code from http://stackoverflow.com/a/14790997)
                            if not any(year in d for d in records[author][2]["years"]):
                                records[author][2]["years"][year] = 1
                            else:
                                records[author][2]["years"][year] += 1
                        
                    elem.clear()
                root.clear()

    records = collections.OrderedDict(sorted(records.items()))

    return records

def topAuthorsRecs(records):
    """ get records of authors with most publication """
    
    # max plot dimensions (for equalising plot dimensions in the browser)
    # "scripts_suggestJS.js" file --> "chartDim" function --> "dataCount" variable
    authorCountMax = 5 # number of top authors to find
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
                journals = collections.OrderedDict(sorted(journals.items(), key=lambda t: t[1]))
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
                                yearsFillGap.insert(startYrIndex + 1, (str(yr), 0))
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
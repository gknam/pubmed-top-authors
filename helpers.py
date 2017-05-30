import collections
import operator
import urllib, json

def getUids(term):
    """Get UIDs for term."""

    # get UIDs from Pubmed
    retmax = 10 # number of articles to fetch
    reldate = 18270 # number of days from now
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&term={}&retmax={}&reldate={}&datetype=pdat&sort=pub+date".format(urllib.parse.quote(term), urllib.parse.quote(str(retmax)), urllib.parse.quote(str(reldate)))
    feed = urllib.request.urlopen(url)
    data = json.loads(feed.read().decode("utf-8"))
    
    # remember UIDs
    uids = []
    for uid in data["esearchresult"]["idlist"]:
        uids.append(uid)
    
    uids = ','.join(uids)

    # return results
    return uids

def getFullRecs(uids):
    """ Get full records from UID """
    
    # get records from Pubmed
    record = [[], [], []]
    records = {}

    # get records from Pubmed
    # 1. using GET method
    try:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={}&retmode=text&rettype=medline".format(uids)
        feed = urllib.request.urlopen(url)
    # 2. using POST method (if uids is too long)
    except urllib.error.HTTPError:
        ids = urllib.parse.urlencode({"id": uids}).encode("utf-8")
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=text&rettype=medline"
        feed = urllib.request.urlopen(url, data=ids)

    data = feed.read().decode("utf-8").splitlines()

    # note key info for each article
    for line in range(len(data)):

        # note author
        if data[line].startswith("FAU - "):
            author = data[line][len("FAU - "):]
            record[0].append(author)
        
        # note publication year
        elif data[line].startswith("DP  - "):
            year = data[line][len("DP  - "):len("DP  - ") + 4]
            record[1].append(year)
        
        # note journal title
        elif data[line].startswith("TA  - "):
            journal = data[line][len("TA  - "):]
            record[2].append(journal)

        # add key info to records at the end of each article
        if data[line].startswith("PMID- ") or (line == len(data) - 1):
            if record == [[], [], []]:
                pass
            else:
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
                    
                    # reset record
                    record = [[], [], []]

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
                yearsFillGap = list(years.items())
                if len(years) > 1:
                    startYr = int(yearsFillGap[0][0])
                    for i in range(0, len(yearsFillGap)):
                        endYr = int(yearsFillGap[i][0])
                        if endYr - startYr > 1:
                            missingYrs = set(range(startYr + 1, endYr))
                            startYrIndex = list(years).index(str(startYr))
                            for yr in missingYrs:
                                yearsFillGap.insert(startYrIndex + 1, (str(yr), 0))
                                topAuthorsRecs[total][rec][author][2]["years"] = dict(yearsFillGap)
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
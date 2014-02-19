import urllib
import os
import re
import time
import sys
import zipfile
from bs4 import BeautifulSoup


tagList = [ 'patent-application-publication', # Enclosing tags
            'document-id>document-date', # Date (published?)
            'title-of-invention', # Title of invention
            'subdoc-abstract>paragraph', # Abstract
            'inventors', # List of inventors
            'subdoc-description>cross-reference-to-related-applications', # Cross reference to related applications
            'domestic-filing-data>application-number>doc-number', # Id number
            'domestic-filing-data>filing-date', # US Date filed
            # PCT Tags
            'foreign-priority-data>filing-date', # PCT Filing Date
            'foreign-priority-data>priority-application-number>doc-number', # PCT Application number

            'cross-reference-to-related-applications>paragraph', # Related Patent Documents
            'subdoc-description>federal-research-statement>paragraph-federal-research-statement', # Government Interest? - Paragraph acknowledging NSF
            'continuity-data>division-of' # Parent Case - cases in <parent-child>? 
            ]
cleanupMode = 0 # Cleanup mode for files: 0 is none, 1 will remove all extracted directory trees, and 2 will remove the directory trees and their zip files

logParsed = False # Useful for debugging, will write all parsed text to file, which is good if the full file is too big to be opened

xmldocs = [] # split_xml saves the split xml lists here 
xmliteration = 0 # Progression through xmldocs

def main():
    # Clear csv file
    clear_file()
    pageurl = 'http://patents.reedtech.com/'
    print 'Getting webpage', pageurl + '...',
    # Get patent urls from webpage
    urls = getUrlList(pageurl + 'parbft.php')
    print 'Done.'
    #urls = [['/pa010315.zip', 'emulate', '.']]
    if not os.path.exists(getwd() + '/temp/'):
        os.makedirs(getwd() + '/temp/')
    i = len(urls) - 1
    # Iterate through urls from oldest to newest, downloading and parsing each one
    while i >= 0:
        url = urls[i]
        tempzip = getwd() + '/temp/' + getUrlFilename(url[0])
        if os.path.isfile(tempzip):
            print 'Found', getUrlFilename(url[0]), 'on disk, not downloading.'
            response = tempzip
        else:
            print 'Downloading', getUrlFilename(url[0]), 'from server.'
            response = (urllib.urlretrieve(pageurl + url[0], tempzip, reporthook))[0]
            print '\n'
        print 'Got response:', '\'' + response + '\''
        
        fulldoc = None
        with zipfile.ZipFile(response, 'r') as myzip:
            xmlname = getUrlFilename(url[0], True) + '.xml'
            # Patent application xml is not always in root, namelist() gets all files within zip
            for filename in myzip.namelist():
                print filename
                if getUrlFilename(filename) == xmlname:
                    print 'Found %s in %s' % (xmlname, response[0])
                    fulldoc = myzip.open(filename)
        

        # Reset xmldocs to an empty list
        global xmldocs
        xmldocs = []
        # Reset xmlinteration to 0
        global xmliteration
        xmliteration = 0
        split_xml(fulldoc)
        scrape_multi(xmldocs=xmldocs)
        
        i-= 1
        # DB - For debugging, break after one iter
        #break



# Get working directory
def getwd():
    return os.path.dirname(os.path.realpath(__file__))


def getUrlFilename(url, remftype=False):
    # Gets the string from the last / character to the end (for example http://patents.reedtech.com/.../ipa140213.zip would return ipa140213.zip
    return url[url.rfind('/') + 1: url.rfind('.') if remftype else len(url)]


# Adapted from http://blog.moleculea.com/2012/10/04/urlretrieve-progres-indicator/
def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = (count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    #import pdb; pdb.set_trace()

    sys.stdout.write("\rProgress: %d%%, %.2f %.2f MB, %d KB/s, %d seconds passed" % (percent, float(progress_size) / (1024 * 1024), float(total_size) / (1024 * 1024), speed, duration))
    sys.stdout.flush()


def getUrlList(url):
    response = urllib.urlopen(url)
    soup = BeautifulSoup(response, ["lxml", "html"])
    result = []
    for table in soup.find_all('table'):
        # If table has class bulktable, then it contains the xml urls
        if table['class'] == ['bulktable']:
            for tr in table.find_all('tr'):
                trVal = []
                # Only find a set number of patent urls (for debugging)
                #if len(result) > 0:
                #    print 'Result', result
                #    return result
                for td in tr.find_all('td'):
                    # Add the trVal to the result. Although trVal is empty, due to how objects work it will still be affected by the tag/text append statements below
                    link = td.find('a')
                    if str(type(link)) == "<class 'bs4.element.Tag'>": 
                        trVal.append(link.get('href'))
                    # If the first <td> is not a url, it must be a heading and should be skipped
                    elif len(trVal) == 0:
                        break
                    # If the data is not a link, then it is either file information or date (in that order), which could be useful
                    else:
                        trVal.append(td.text)
                
                # If nothing of value was found, do not add the values to the result
                if len(trVal) > 0:
                    result.append(trVal)
    return result 


# The parser will not parse past the second dtd statement, so this will split each xml segment into its own file in memory
def split_xml(fulldoc):
    xml = []
    lnum = 0
    n_iter = 0
    print 'Splitting xml, please wait...'
    for line in fulldoc:
        lnum += 1
        xml.append(line)
        if (line.strip().find(formatTag(tagList[0], True)) >= 0):
            # Clone the list and append it to xmldocs
            xmldocs.append(list(xml))
            # Write to file (should be commmented out, for debugging purposes
            if logParsed:
                f = open(getwd() + '/output.csv', 'a') 
                f.write(''.join(xml))
            n_iter += 1
            xml = []
            sys.stdout.write("\rSplit %d on line %d ..." % (n_iter, lnum))
            sys.stdout.flush()

            # Debug Break-If this is uncommented, it will split only a set maximum of times
            #if (n_iter > 10):
            #    return 
    print 'Done with length %d.' % len(xmldocs)


def formatTag(tag, close=False):
    # Remove the tag tree data from the string and enclose it in <>, with an optional /
    return  ('</' if close else '<') + tag[ tag.rfind('>') + 1: ] + '>'


def scrape_multi(xmldocs):
    print 'Beginning scrape of %s documents' % len(xmldocs)
    for xml in xmldocs:
        scrape(xml)
        global xmliteration
        xmliteration += 1


def scrape(xmllist):
    sys.stdout.write("\rScraping %s of %s." % (xmliteration + 1, len(xmldocs))),
    sys.stdout.flush()
    
    # Gets the government interest field and looks for NSF or national science foundation
    if (get_govt_interest(xmllist)):
        print 'Found NSF reference, adding to CSV. <!!!!!!!!!!!'
    else:
        return 
    # Create a string from the singular xml list created in split_xml()
    xml = '\n'.join(xmllist)
    soup = BeautifulSoup(xml, ["lxml", "xml"])

    # List all scraped data will be stored in
    datalist = []

    for tag in tagList:
        datalist.append(parse_xml(soup, tag))
    write_data(datalist)


# get Govt Interest without using lxml (prevents a whole xml tree structure from needing to be parsed and created)
def get_govt_interest(xmllist):
    opentag = False
    for line in xmllist:
        startpos = line.find('<paragraph-federal-research-statement>')
        endpos = line.find('</paragraph-federal-research-statement>')
        if startpos >= 0:
            opentag = True

        if opentag == True:
            standardline = re.sub("[^a-zA-Z0-9]", "", line).lower() 
            
            # If the start or end pos is on the current line, only look at the portion of the line within the tags
            if startpos >= 0: standardline = standardline[startpos :]
            if endpos >= 0: standardline = standardline[: endpos]

            if (standardline.find('nsf') >= 0 or standardline.find('nationalsciencefoundation') >= 0):
                return True
        if endpos >= 0:
            return False
    return False


def parse_xml(soup, tag):
    finaltag = None #The tag object which will be printed or returned at the end of the scrape
    result = 'None'
    #print '=======Now searching tag', tag + '======='
    
    # (Re)sets subsoup to the top of the xml tree
    subsoup = soup.find('patent-application-publication')
    tagtree = tag.split('>')
    if len(tagtree) > 1:
        #print 'tagtree length:', len(tagtree)
        for i in xrange(0, len(tagtree)):
            #print i, tagtree[i]
            if subsoup == None:
                #print 'WARNING: \'' + tagtree[i - 1] + '\' is none in tag tree:', ', '.join(tagtree)
                result = 'None'
                break
            elif i < len(tagtree) - 1:
                #print i, '<', len(tagtree), 'adding', tagtree[i], 'to tree.'
                subsoup = subsoup.find(tagtree[i])
            else:
                finaltag = subsoup.find(tagtree[i])
                #print 'finaltag', finaltag
                #print 'Found (in tree):', tagString(finaltag)
                #print tagTreeString(finaltag)
                result = tagString(finaltag)

    else:
        finaltag = subsoup.find(tag)
        # Add special formatting for inventors tag
        if tag == 'inventors':
            #print finaltag.prettify()
            templist = []
            if finaltag != None:
                for descend in finaltag.descendants:
        
                    #print 'descend', descend, 'type:', type(descend)
                    # Find opening tag for new inventors by checking if element is a tag which contains the string 'inventor' but not 'inventors'
                    if tag_name_contains(descend, 'inventor'):
                        #print 'Found inventor', descend,  ',', descend.name
                        if len(templist) > 0:
                            # Add a closing bracket for a previous element if one exists
                            templist.append(']')

                        templist.append('[')
                        templist.append(tagString(descend).strip())
                # Add a final closing bracket
                if len(templist) > 0 and templist[-1] != ']':
                    templist.append(']')
                #print templist
                result = ''.join(templist)
            else:                
                result = tagString(finaltag)
    
    #print type(result), result
    return unicode(result)


def tagString(tag):
    result = ''
    if (tag == None):
        result = 'None'
    elif (tag.string == None):
         result = tag.get_text(' ')
    else:
        result = tag.string 
    return result


def tagTreeString(tag):
    tree = ''
    if tag == None or tag.parents == None:
        return 'None'
    for parenttag in tag.parents:
        if (parenttag.name != None):
            tree = '<' + parenttag.name + '> ' + tree
    return tree


# Put in own method to make logic less cluttered
def tag_name_contains(descend, string):
    return descend != None and str(type(descend)) == '<class \'bs4.element.Tag\'>' and descend.name != None and descend.name.find(string) != -1


def write_output(f, output_str):
    # If line doesn't already have line break at end, add one
    if len(output_str) > 0 and output_str[-1] != '\n':
        f.write(output_str + '\n')
    else:
        f.write(output_str)


def setup_datalist(datalist):
    for i in xrange(0, len(datalist)):
        data = datalist[i].strip()
        # Fix for inventors tag having newline characters
        if data.find(' ') > 0:
            data = '\'' + data + '\''
        datalist[i] = data
    return datalist


def clear_file():
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/output.csv', 'w') 
    f.write('')
    f.close()


def write_data(datalist):
    count = 0
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/output.csv', 'a') 
    
    for i in xrange(0, len(datalist)):
        datalist[i] = (datalist[i].replace(' \n \n \n ', ' - '))
        datalist[i] = (datalist[i].replace('\n', ''))
        
    
    datalist = setup_datalist(datalist) 
    output = ', '.join(datalist)
    #print output
    write_output(f=f, output_str=output)
    #write_output(f=f, output_str='-')
    count += 1

    f.close()

if __name__ == '__main__':
    start = time.clock()
    main()
    elapsed = (time.clock() - start)
    print '\nTime elapsed:', elapsed

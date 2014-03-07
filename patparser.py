from bs4 import BeautifulSoup
import urllib
import sys
import re

'''tagList = [ 'patent-application-publication', # Enclosing tags
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
            ]'''

tagList = [ 'us-patent-application',
            'date-publ', 
            'invention-title',
            'abstract',
            'us-parties>inventors',
            'us-related-documents', #?
            'document-id>doc-number',
            #US filing date
            'pct-or-regional-filing-data>document-id>date', #?
            'pct-or-regional-filing-data>document-id>doc-number', #?
            'pct-or-regional-filing-data>us-371c124-date',
            'pct-or-regional-publishing-data>document-id>doc-number', #?
            'pct-or-regional-publishing-data>document-id>date', #?
            'related-publication',
            'us-related-documents', #?
            #Govt interest?
            'parent-doc' #?
            ]


xmldocs = [] # split_xml saves the split xml lists here 
xmliteration = 0 # Progression through xmldocs

# Will contain sets of the relevant scraped tags
datalists = []

file_writer = None

def bindFileWriter(fw):
    global file_writer
    file_writer = fw
    print 'Successfully bound file writer instance'

def getUrlList(url, sort=True):
    response = urllib.urlopen(url)
    soup = BeautifulSoup(response, ["lxml", "html"])
    result = []
    # Google downloading
    for link in soup.find_all('a'):
        if link.text.strip()[:3] == 'ipa' or link.text.strip()[:2] == 'pa':
            result.append(link.get('href'))
            #print 'Appending %s' % link.get('href')
    if sort: result = sorted(result, key=lambda str: re.sub('[^0-9]', '', str))
    return result 

# The parser will not parse past the second dtd statement, so this will split each xml segment into its own file in memory
def split_xml(fulldoc):
    xml = []
    lnum = 0
    n_iter = 0
    print 'Splitting xml, please wait...'
    
    found = False
    for line in fulldoc:
        lnum += 1
        xml.append(line)
        
        # Try and find where the tag changes so I can patch it in
        if line.strip().find(formatTag(tagList[0])) >= 0:
            found = True

        if (line.strip().find(formatTag(tagList[0], True)) >= 0):
            # Clone the list and append it to xmldocs
            xmldocs.append(list(xml))
            # Write to file (should be commmented out, for debugging purposes
            #f = open(getwd() + '/output.csv', 'a') 
            #f.write(''.join(xml))
            n_iter += 1
            xml = []
            sys.stdout.write("\rSplit %d on line %d ..." % (n_iter, lnum))
            sys.stdout.flush()
            if n_iter >= 393:
                break
            

    print 'Done with length %d.' % len(xmldocs)

def scrape_multi():
    #print 'Beginning scrape of %s documents' % len(xmldocs)
    for xml in xmldocs:
        #Add data to datalist
        datalists.append(scrape(xml))
        global xmliteration
        xmliteration += 1
    # Add line return to output
    print ''


def scrape(xmllist):
    sys.stdout.write("\rScraping %s of %s." % (xmliteration + 1, len(xmldocs)))
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

    return datalist


# get Govt Interest without using lxml (prevents a whole xml tree structure from needing to be parsed and created)
def get_govt_interest(xmllist):
    opentag = False
    #print 'Looking for govt interest...'
    for line in xmllist:
        startpos = line.find('<federal-research-statement>')
        endpos = line.find('</federal-research-statement>')
        if startpos >= 0:
            opentag = True

        if opentag == True:
            standardline = re.sub("[^a-zA-Z0-9 ]", "", line).lower() # Remove non alphanumerics or spaces
            
            #print 'Govt interest:', line
            
            # If the start or end pos is on the current line, only look at the portion of the line within the tags
            if startpos >= 0: 
                standardline = standardline[startpos :]
            if endpos >= 0: standardline = standardline[: endpos]
            
            # Keep only alphanumerics/spaces when searching for the abbreviation, and only keep alphanumerics when searching for the full name
            if (standardline.find('nsf') >= 0 or re.sub('[ ]', '', standardline).find('nationalsciencefoundation') >= 0):
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
                for name in finaltag.find_all('name'):
                    print name
                    templist.append('[')
                    i = 0
                    for namepart in name.children:
                        # Append all strings
                        print namepart, str(type(namepart))
                        if str(type(namepart)) == '<class \'bs4.element.Tag\'>':
                            if i > 0:
                                templist.append(' ')
                            print 'Appending' + namepart.string
                            templist.append(namepart.string.strip())
                            i += 1
                    
                    templist.append(']')
                result = ''.join(templist)
            else:                
                result = tagString(finaltag)
    
    #print type(result), result
    return [tag, unicode(result)]


# Put in own method to make logic less cluttered
def tag_name_contains(descend, string):
    return descend != None and str(type(descend)) == '<class \'bs4.element.Tag\'>' and descend.name != None and descend.name.find(string) != -1


def formatTag(tag, close=False):
    # Remove the tag tree data from the string and enclose it in <>, with an optional /
    return  ('</' if close else '<') + tag[ tag.rfind('>') + 1: ] + '>'


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

if __name__ == '__main__':
    print 'This is not runnable code.'

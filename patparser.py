from bs4 import BeautifulSoup
import urllib
import sys
import re

import patutil

class Tags():

    def setTags(self, year):
        self.test_var = 'Test Variable'

        if year >= 0: # These tags will probably not work correctly.  The program is only designed for 2007 DTD standard and above 
            self.ipa_enclosing = 'patent-application-publication', # Enclosing tags
            self.ipa_pubdate = 'document-id/document-date', # Date (published?)
            self.ipa_invtitle = 'title-of-invention', # Title of invention
            self.ipa_abstract = 'subdoc-abstract/paragraph', # Abstract
            self.ipa_inventors = 'inventors', # List of inventors
            self.ipa_crossref = 'subdoc-description/cross-reference-to-related-applications/paragraph', # Cross reference to related applications
            self.ipa_appnum = 'domestic-filing-data/application-number/doc-number', # Id number
            self.ipa_appdate = 'domestic-filing-data/filing-date', # US Date filed
            self.ipa_pct_filedate = 'foreign-priority-data/filing-date', # PCT Filing Date
            self.ipa_pct_pubnum = 'foreign-priority-data/priority-application-number/doc-number', # PCT Application number
            self.ipa_govint = 'subdoc-description/federal-research-statement/paragraph-federal-research-statement', # Government Interest? - Paragraph acknowledging NSF
            self.ipa_parentcase = 'continuity-data/division-of' # Parent Case - cases in <parent-child/? 

        if year >= 07:
            # 2007 tagslist
            self.ipa_enclosing = 'us-patent-application'
            self.ipa_pubdate = 'publication-reference/document-id/date' #Published patent document
            self.ipa_invtitle = 'invention-title' #Title of invention
            self.ipa_abstract = 'abstract/p' # Concise summary of disclosure
            self.ipa_inventors = 'applicants' # Applicants information
            self.ipa_crossref = '<?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="lead"?><?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="tail"?>' #
            self.ipa_appnum = 'application-reference/document-id/doc-number' # Patent ID
            self.ipa_appdate = 'application-reference/document-id/date' # Patent ID Date or something
            self.ipa_pct_filedate = 'pct-or-regional-filing-data/document-id/date' #
            self.ipa_pct_filenum = 'pct-or-regional-filing-data/document-id/doc-number' #PCT filing number
            self.ipa_pct_371cdate = 'pct-or-regional-filing-data/us-371c124-date' # PCT filing date
            self.ipa_pct_pubnum = 'pct-or-regional-publishing-data/document-id/doc-number' # PCT publishing date
            self.ipa_pct_pubdate = 'pct-or-regional-publishing-data/document-id/date' # PCT publishing date
            self.ipa_priorpub = 'related-publication/document-id/doc-number' # Previously published document about same app
            self.ipa_priorpubdate = 'related-publication/document-id/date' # Date for previously published document
            self.ipa_govint = '<?federal-research-statement description="Federal Research Statement" end="lead"?><?federal-research-statement description="Federal Research Statement" end="tail"?>' #Govt interest?
            self.ipa_parentcase = 'us-related-documents/parent-doc/document-id/doc-number' # Parent Case
            self.ipa_childcase = 'us-related-documents/child-doc/document-id/doc-number' # Child Case

            '''# 2007 Patent grant (Needs work)
            self.ipa_enclosing = 'us-patent-application'
            self.ipa_pubdate = 'publication-reference/document-id/date' #Published patent document
            self.ipa_invtitle = 'invention-title' #Title of invention
            self.ipa_abstract = 'abstract/p' # Concise summary of disclosure
            self.ipa_inventors = 'applicants' # Applicants information
            self.ipa_crossref = '<?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="lead"?><?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="tail"?>' #
            self.ipa_appnum = 'application-reference/document-id/doc-number' # Patent ID
            self.ipa_appdate = 'application-reference/document-id/date' # Patent ID Date or something
            self.ipa_pct_filedate = 'pct-or-regional-filing-data/document-id/date' #
            self.ipa_pct_filenum = 'pct-or-regional-filing-data/document-id/doc-number' #PCT filing number
            self.ipa_pct_371cdate = 'pct-or-regional-filing-data/us-371c124-date' # PCT filing date
            self.ipa_pct_pubnum = 'pct-or-regional-publishing-data/document-id/doc-number' # PCT publishing date
            self.ipa_pct_pubdate = 'pct-or-regional-publishing-data/document-id/date' # PCT publishing date
            self.ipa_priorpub = 'related-publication/document-id/doc-number' # Previously published document about same app
            self.ipa_priorpubdate = 'related-publication/document-id/date' # Date for previously published document
            self.ipa_govint = '<?federal-research-statement description="Federal Research Statement" end="lead"?><?federal-research-statement description="Federal Research Statement" end="tail"?>' #Govt interest?
            self.ipa_parentcase = 'us-related-documents/parent-doc/document-id/doc-number' # Parent Case
            self.ipa_childcase = 'us-related-documents/child-doc/document-id/doc-number' # Child Case'''
        
        if year >= 12:
            # Figure this out
            self.ipa_inventors = 'us-parties/inventors'
    
    def getAppTags(self, year):
        self.setTags(year)

        return [self.ipa_pubdate,
                self.ipa_invtitle,
                self.ipa_abstract,
                self.ipa_inventors,
                self.ipa_crossref,
                self.ipa_appnum,
                self.ipa_appdate,
                self.ipa_pct_filedate,
                self.ipa_pct_filenum,
                self.ipa_pct_371cdate,
                self.ipa_pct_pubnum,
                self.ipa_pct_pubdate,
                self.ipa_priorpub,
                self.ipa_priorpubdate,
                self.ipa_govint,
                self.ipa_parentcase,
                self.ipa_childcase]
        #return self.getTags(year, 'ipa_')

    def getGrantTags(self, year):
        return self.getTags(year, 'ipg_')

    # Get all variables in Tags that start with a prefix and append the values to a list
    def getTags(self, year, prefix):
        self.setTags(year)
        
        tagsList = []
        for var in iter(self.__dict__):
             #print b
             if var[:len(prefix)] == prefix:
                 tagsList.append(self.__dict__.get(var))

        return tagsList
        

xmldocs = [] # split_xml saves the split xml lists here 
xmliteration = 0 # Progression through xmldocs

# Will contain sets of the relevant scraped tags
datalists = []

file_writer = None

tags = Tags()

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
        if line.strip().find(formatTag(tags.ipa_enclosing)) >= 0:
            found = True

        if (line.strip().find(formatTag(tags.ipa_enclosing, True)) >= 0):
            # Clone the list and append it to xmldocs
            xmldocs.append(list(xml))
            # Write to file (should be commmented out, for debugging purposes
            #f = open(getwd() + '/output.csv', 'a') 
            #f.write(''.join(xml))
            n_iter += 1
            xml = []
            sys.stdout.write("\rSplit %d on line %d ..." % (n_iter, lnum))
            sys.stdout.flush()
            if n_iter >= 254:
                break
            
    print 'Done with length %d.' % len(xmldocs)

def scrape_multi(year_):
    global year
    year = year_

    for xml in xmldocs:
        #Add data to datalist
        data = scrape(xml)
        datalists.append(data)
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

    global tags
    for tag in tags.getAppTags(year):
        # Non bs4 parsing
        if (tag[0:2] == '<?'):
            # Split start and end tags
            split = tag.find('>') + 1
            tagpair = (tag[0:split], tag[split:])
            #print tags
            datalist.append([tag, strfind_tag(tagpair[0], tagpair[1], xmllist)])
        else:
            datalist.append([tag, parse_xml(soup, tag)])

    return datalist


def get_govt_interest(xmllist):
    standardline = strfind_tag('<?federal-research-statement description="Federal Research Statement" end="lead"?>','<?federal-research-statement description="Federal Research Statement" end="tail"?>', xmllist)
    
    #print 'Final text',standardline
    if standardline == None:
        return False

    standardline = re.sub("[^a-zA-Z0-9 ]", "", standardline).lower() # Remove non alphanumerics or spaces

    # Keep only alphanumerics/spaces when searching for the abbreviation, and only keep alphanumerics when searching for the full name
    if (standardline.find('nsf') >= 0 or re.sub('[ ]', '', standardline).find('nationalsciencefoundation') >= 0):
        return True

    return False



# get Govt Interest without using lxml (prevents a whole xml tree structure from needing to be parsed and created)
def strfind_tag(starttag, endtag, xmllist):
    opentag = False
    result = ''
    for line in xmllist:
        startpos = line.find(starttag)
        endpos = line.find(endtag)
        if startpos >= 0:
            opentag = True

        if opentag == True:           
            text = line
            # If the start or end pos is on the current line, only look at the portion of the line within the tags
            if startpos >= 0: 
                text = text[startpos:]
            if endpos >= 0: 
                # Get substring within tag (subtract startpos in order to remove the offset introduced above
                text = text[: endpos]
            
            result += text
            #print 'Result "%s", startpos %s, endpos %s' % (text, startpos, endpos)

        # Return text within the <p> element (for CROSS REFERENCE and GOVERNMENT INTEREST) this works.
        if endpos >= 0:
            # Without the enclosing tags, it will only recognize the first tag within the result.
            endresult = '<_enclosing>' + result[len(starttag) : ] + '</_enclosing>'
            print endresult
            return unicode(BeautifulSoup(endresult, ['lxml', 'xml']).find('p').get_text())
    return 'None'


def parse_xml(soup, tag):
    global tags
    finaltag = None #The tag object which will be printed or returned at the end of the scrape
    result = 'None'
    print '=======Now searching tag', tag + '======='
     
    # (Re)sets subsoup to the top of the xml tree
    #print tags
    subsoup = soup.find(tags.ipa_enclosing)
    tagtree = tag.split('/')
    #print 'tagtree length:', len(tagtree)
    for i in xrange(0, len(tagtree)):
        if subsoup == None:
            #print 'WARNING: \'' + tagtree[i - 1] + '\' is none in tag tree:', ', '.join(tagtree)
            result = 'None'
            break

        elif i < len(tagtree) - 1: # If not at the end of the tree
            subsoup = subsoup.find(tagtree[i])

        else: # If at the end of the tree (or if the tree only has one element)
            finaltag = subsoup.find(tagtree[i])
            result = tagString(finaltag)

            # Add special formatting for inventors tag
            if tag == 'applicants':
                templist = []
                if finaltag != None:
                    for name in finaltag.find_all('addressbook'):
                        #print name
                        templist.append('[')
                        i = 0
                        # Only append if tag contains name (first-name), (last-name), etc.
                        # Iterative
                        '''for namepart in name.children:
                            if str(type(namepart)) == '<class \'bs4.element.Tag\'>' and namepart.name.find('name') >= 0:
                                print namepart, str(type(namepart))
                                # Append all strings
                                if i > 0:
                                    templist.append(' ')
                                print 'Appending' + namepart.string
                                templist.append(namepart.string.strip())
                                i += 1'''
                        # Hard coded
                        templist.append(name.find('first-name').string)
                        if (name.find('middle-name') != None):
                            templist.append(' ' + name.find('middle-name').string)
                        templist.append(' ' + name.find('last-name').string)
                            
                        templist.append(']')
                
                    result = ''.join(templist)

    #print type(result), result
    return unicode(result)


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

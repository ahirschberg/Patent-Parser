from bs4 import BeautifulSoup
import urllib
import sys
import re
import time

import patutil

class Tags:

    def __init__(self):
        self.ptype = None

    def setTags(self, year):
        print 'Year is %s' % year
        if year >= 07:
            # 2007 tagslist
            self.ipa_enclosing = 'us-patent-application'
            self.ipa_pubnum = 'publication-reference/document-id/doc-number'
            self.ipa_pubdate = 'publication-reference/document-id/date' #Published patent document
            self.ipa_invtitle = 'invention-title' #Title of invention
            self.ipa_abstract = 'abstract/p' # Concise summary of disclosure
            self.ipa_assignee = 'assignees/assignee'
            self.ipa_inventors = 'applicants' # Applicants information
            self.ipa_crossref = '<?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="lead"?><?cross-reference-to-related-applications description="Cross Reference To Related Applications" end="tail"?>' # Xref, but there is also a 2nd option coded into the scrape method
            self.ipa_appnum = 'application-reference/document-id/doc-number' # Patent ID
            self.ipa_appdate = 'application-reference/document-id/date' # Filing Date
            self.ipa_pct_371cdate = 'pct-or-regional-filing-data/us-371c124-date' # PCT filing date
            self.ipa_pct_pubnum = 'pct-or-regional-publishing-data/document-id/doc-number' # PCT publishing date
            self.ipa_priorpub = 'related-publication/document-id/doc-number' # Previously published document about same app
            self.ipa_priorpubdate = 'related-publication/document-id/date' # Date for previously published document
            self.ipa_govint = '<?federal-research-statement description="Federal Research Statement" end="lead"?><?federal-research-statement description="Federal Research Statement" end="tail"?>' #Govint
            self.ipa_parentcase = 'us-related-documents/parent-doc/document-id/doc-number' # Parent Case
            self.ipa_childcase = 'us-related-documents/child-doc/document-id/doc-number' # Child Case

            self.ipg_enclosing = 'us-patent-grant'
            self.ipg_govint = '<?GOVINT description="Government Interest" end="lead"?><?GOVINT description="Government Interest" end="tail"?>'
            self.ipg_crossref = '<?RELAPP description="Other Patent Relations" end="lead"?><?RELAPP description="Other Patent Relations" end="tail"?>'

        if year >= 12:
            self.ipa_inventors = 'us-applicants'
        
    def getAppTags(self, year):
        self.setTags(year)

        return [self.ipa_appnum,
                self.ipa_pubdate,
                self.ipa_pubnum,
                self.ipa_invtitle,
                self.ipa_abstract,
                self.ipa_inventors,
                self.ipa_assignee,
                self.ipa_crossref,
                self.ipa_appdate, # File date
                self.ipa_govint,
                self.ipa_parentcase,
                self.ipa_childcase,
                self.ipa_pct_371cdate,
                self.ipa_pct_pubnum]
  
   
    def getHeadings(self):
        return ['appnum',
                'pubdate',
                'pubnum',
                'invtitle',
                'abstract',
                'inventors',
                'assignee',
                'crossref',
                'appdate', # File date
                'govint',
                'parentcase',
                'childcase',
                'pct_371cdate',
                'pct_pubnum']

    # Grant tags that are equivalent to application tags are not duplicated.
    def getGrantTags(self, year):
        return [self.ipa_appnum,
                self.ipa_pubdate,
                self.ipa_pubnum,
                self.ipa_invtitle,
                self.ipa_abstract,
                self.ipa_inventors,
                self.ipa_assignee,
                self.ipg_crossref,
                self.ipa_appdate, # File date (not sure if interpreting ruby parser's xpath correctly.)
                self.ipg_govint,
                self.ipa_parentcase,
                self.ipa_childcase,
                self.ipa_pct_371cdate,
                self.ipa_pct_pubnum]

    def getTags(self, year):
        if patutil.cmd_args['ptype'] == 'a':
            return self.getAppTags(year)
        elif patutil.cmd_args['ptype'] == 'g':
            return self.getGrantTags(year)

    # Convenience method to get the enclosing tag for whichever mode is being used
    def getEnclosing(self):
        if patutil.cmd_args['ptype'] == 'a': return tags.ipa_enclosing
        elif patutil.cmd_args['ptype'] == 'g': return tags.ipg_enclosing 
        else: return None


xmldocs = [] # split_xml saves the split xml lists here 
xmliteration = 0 # Progression through xmldocs

# Will contain sets of the relevant scraped tags
datalists = []

file_writer = None

tags = Tags()

def getUrlList(url, ptype, sort=True):
    response = urllib.urlopen(url)
    soup = BeautifulSoup(response, ["lxml", "html"])
    result = []
    
    # Google downloading
    for link in soup.find_all('a'):
        if link.text.strip()[:3] == ('ip' + ptype) or link.text.strip()[:2] == ('p' + ptype):
            result.append(link.get('href'))
            #print 'Appending %s' % link.get('href')

    if sort: result = sorted(result, key=lambda str: re.sub('[^0-9]', '', str))
    return result 


# The parser will not parse past the second dtd statement, so this will split each xml segment into its own file in memory
def split_xml(fulldoc, max_iter=(-1)):
    xml = []
    lnum = 1
    n_iter = 1
    print max_iter
    print 'Splitting xml, please wait...'
    
    found = False
    for line in fulldoc:
        enclosing = tags.getEnclosing()
        if line.find(formatTag(enclosing)[:-1]) >= 0:
            found = True

        if found: # Sometimes there is data outside the ipa_enclosing tags which messes up the parser.
            xml.append(line)

        if (line.strip().find(formatTag(enclosing, True)) >= 0):
            found = False
            # Clone the list and append it to xmldocs
            xmldocs.append(list(xml))
            # Write to file (should be commmented out, for debugging purposes
            #f = open(getwd() + '/output.csv', 'a') 
            #f.write(''.join(xml))
            n_iter += 1
            xml = []
            patutil.print_over("\rSplit %d on line %d ..." % (n_iter, lnum))
            if max_iter >= 0 and n_iter > max_iter:
                break

        lnum += 1
            
    print 'Done with length %d.' % len(xmldocs)

def scrape_multi(year_, nonsf_flag=False):
    global year
    year = year_

    for xml in xmldocs:
        if patutil.cmd_args['max_nsf'] >= 0 and patutil.cmd_args['max_nsf'] <= len(datalists):
            break
        #Add data to datalist
        data = scrape(xml, nonsf_flag)
        if data != None:
            datalists.append(data)
        global xmliteration
        xmliteration += 1
    # Add line return to output
    print ''


def scrape(xmllist, nonsf_flag=False):
    patutil.print_over("\rScraping %s of %s." % (xmliteration + 1, len(xmldocs)))
    
    # Gets the government interest field and looks for NSF or national science foundation
    if (get_govt_interest(xmllist)):
        print 'Found NSF reference, adding to CSV. <!!!!!!!!!!!'
    elif not nonsf_flag:
        return 
    xml = ''.join(xmllist)

    # Create a string from the singular xml list created in split_xml()
    if patutil.cmd_args['dump_flag']:
        patutil.dump_xml(xml, str(xmliteration) + '.xml')

    # Begin the parse
    soup = BeautifulSoup(xml, ["lxml", "xml"])
    datalist = []

    global tags
    for tag in tags.getTags(year):
        # Non bs4 parsing
        if (tag[0:2] == '<?'):
            # Split start and end tags
            split = tag.find('>') + 1
            tagpair = (tag[0:split], tag[split:])
            strfind_result = strfind_tag(tagpair[0], tagpair[1], xmllist)

            # Hack for alternate way to get cross reference in patent grants in the description element (not sure if interpreting ruby parser's xpath correctly.)
            if tag != tags.ipg_crossref or (tag == tags.ipg_crossref and strfind_result != None):
                datalist.append([tag, strfind_result])
            else:
                desc = soup.find('description')
                if re.sub('[^a-z]', '', desc.find('heading').string.lower()).find('crossref') >= 0:
                    text = desc.string
                    print text
                    datalist.append([tag, text])
                else: datalist.append([tag, 'None'])
        else:
            datalist.append([tag, parse_xml(soup, tag)])

    return datalist


def get_govt_interest(xmllist):
    govint_pair = None
    # This could be consolidated into one set of string manipulations.
    if patutil.cmd_args['ptype'] == 'a':
        split = tags.ipa_govint.find('>') + 1
        govint_pair = (tags.ipa_govint[0:split], tags.ipa_govint[split:])
    elif patutil.cmd_args['ptype'] == 'g':
        split = tags.ipg_govint.find('>') + 1
        govint_pair = (tags.ipg_govint[0:split], tags.ipg_govint[split:])

    standardline = strfind_tag(govint_pair[0], govint_pair[1], xmllist)
    
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
            #print endresult
            return unicode(BeautifulSoup(endresult, ['lxml', 'xml']).find('p').get_text())
    return 'None'


def parse_xml(soup, tag):
    global tags
    finaltag = None #The tag object which will be printed or returned at the end of the scrape
    result = 'None'
    #patutil.print_over('\rScraping tag %s.' % (tag))
    print 'Scraping tag %s.' % tag 
    # (Re)sets subsoup to the top of the xml tree
    enclosing = tags.getEnclosing() 
    subsoup = soup.find(enclosing)
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

            # Below methods assume that the ipa and ipg variables being worked with are the same
            # Add special formatting for inventors tag
            if tag == tags.ipa_inventors:
                print 'Tag was inventors'
                templist = []
                if finaltag != None:
                    for name in finaltag.find_all('addressbook'):
                        #print name
                        templist.append('[')
                        # Only append if tag contains name (first-name), (last-name), etc.
                        templist.append(name.find('first-name').string)
                        if (name.find('middle-name') != None):
                            templist.append(' ' + name.find('middle-name').string)
                        templist.append(' ' + name.find('last-name').string)
                        templist.append(']')
                
                    result = ''.join(templist)
            elif tag == tags.ipa_assignee:
                templist = []
                if finaltag != None:
                    for name in finaltag.find_all('addressbook'):
                        #print name
                        templist.append('[')
                        templist.append(name.find('orgname').string)
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

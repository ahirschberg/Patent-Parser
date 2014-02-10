import urllib
import os
import re
import zipfile
from bs4 import BeautifulSoup


#
# Change tagList[10] when you add new tags!
#
tagList = [ 'document-id>document-date', #Date (published?)
            'title-of-invention', #Title of invention
            'subdoc-abstract>paragraph', #Abstract
            'inventors', #List of inventors
            'subdoc-description>cross-reference-to-related-applications', #Cross reference to related applications
            'domestic-filing-data>application-number>doc-number', #Id number
            'domestic-filing-data>filing-date', #US Date filed
            #PCT Tags
            'foreign-priority-data>filing-date', #PCT Filing Date
            'foreign-priority-data>priority-application-number>doc-number', #PCT Application number

            'cross-reference-to-related-applications>paragraph', #Related Patent Documents
            'subdoc-description>federal-research-statement>paragraph-federal-research-statement', #Government Interest? - Paragraph acknowledging NSF
            'continuity-data>division-of' #Parent Case - cases in <parent-child>? 
            ]


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

#response = urllib.urlopen("http://patents.reedtech.com/downloads/ApplicationFullText/2001/pa011227.zip")
print 'Getting zip file'
#fulldoczip = response.read()
with zipfile.ZipFile(open(os.path.dirname(os.path.realpath(__file__)) + '/pa011227.zip'), 'r') as myzip:
    fulldoc = myzip.open('pa011227.xml')
#print("Got xml from server")
#fulldoc = open(os.path.dirname(os.path.realpath(__file__)) + '/2002-10-03applications.xml')
xmldocs = []
iteration = 0

# The parser will not parse past the second dtd statement, so this will split each xml segment into its own file in memory
def split_xml(fulldoc):
    xml = []
    lnum = 0
    n_iter = 0
    for line in fulldoc:
        lnum += 1
        xml.append(line)
        if (line.strip() == '</patent-application-publication>'):
            # Clone the list and append it to xmldocs
            xmldocs.append(list(xml))
            print 'xml', len(xml)
            n_iter += 1
            xml = []
            if (n_iter > 10):
                return #If this is uncommented, it will split only once
    print 'xmldocs', len(xmldocs)


def scrape_multi(xmldocs):
    #scrape(xmllist=xmldocs[0])
    for xml in xmldocs:
        scrape(xml)
        global iteration
        iteration += 1

def scrape(xmllist):
    xml = '\n'.join(xmllist)
    print 'Parsing xml with length', len(xml)
    soup = BeautifulSoup(xml, ["lxml", "xml"])
    # List all scraped data will be stored in
    datalist = []
    print '===========================\n      Starting Scrape (%s lines)      \n===========================' % soup.prettify().count('\n')
    
    # Change number here as you add new tags
    # Does not work VVVVVVVVVV
    govtInterestClause = parse_xml(soup, tagList[10]).lower()
    print govtInterestClause
    govtInterestClause = re.sub("[^a-zA-Z0-9]", "", govtInterestClause); 
    print govtInterestClause 
    if (govtInterestClause.find('NSF') == -1 and govtInterestClause.find('National Science Foundation') == -1):
        print '======== NO NSF IN GOVT INTEREST CLAUSE, RETURNING ======='
        return
    for tag in tagList:
        datalist.append(parse_xml(soup, tag))
    write_data(datalist)

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
    
    return result

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


def write_data(datalist):
    count = 0
    writemode = 'w'
    if (iteration > 0):
        writemode = 'a'
    f = open(os.path.dirname(os.path.realpath(__file__)) + '/output.csv', writemode) 
    #print f
    header = '====Document %s, length %s====' % (count, len(datalist)) 
    #print header
    #write_output(f, header)
    
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


split_xml(fulldoc)
scrape_multi(xmldocs=xmldocs)


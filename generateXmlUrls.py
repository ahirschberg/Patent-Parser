import urllib
from bs4 import BeautifulSoup

print 'Getting webpage'
response = urllib.urlopen('http://patents.reedtech.com/parbft.php')
soup = BeautifulSoup(response, ["lxml", "html"])
result = []
for table in soup.find_all('table'):
    #print table['class']
    if table['class'] == ['bulktable']:
        for tr in table.find_all('tr'):
            trVal = []
            for td in tr.find_all('td'):
                result.append(trVal)
                #print td
                link = td.find('a')
                #print type(link), link
                if str(type(link)) == "<class 'bs4.element.Tag'>": 
                    print 'Appending', link.get('href')
                    trVal.append(link.get('href'))
                # If the first <td> is not a url, it must be a heading and should be skipped
                elif len(trVal) == 0:
                    break
                else:
                    print 'Appending', td.text
                    trVal.append(td.text)
#Print result
for trVal in result:
    print ', '.join(trVal)   
#import pdb; pdb.set_trace()

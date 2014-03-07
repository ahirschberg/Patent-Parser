import urllib
import os
import re
import time
import sys
import signal
import zipfile
import patparser

# For safely exiting after a scrape, not during it
scraping = False
break_scrape = False

download_directory = '/temp/'

file_writer = None 

def main():
    # Clear csv file
    #file_writer.clear_file()

    # Get patent urls from webpage
    pageurl = 'https://www.google.com/googlebooks/uspto-patents-applications-text.html'
    print 'Getting webpage', pageurl + '...',
    urls = []

    for url in patparser.getUrlList(pageurl):
        if int(splitDate(url, True)[0]) >= 7:
            urls.append(url)
    #urls = ['pa010531.zip']
    
    numremoved = 0#removeDownloaded(urls)
    print 'Found %d urls (%d removed because they were already downloaded)' % (len(urls), numremoved)
    if not os.path.exists(getwd() + download_directory):
        os.makedirs(getwd() + download_directory)
    i = 0
    # Iterate through urls from oldest to newest, downloading and parsing each one
    while i < len(urls):
        # Reset xmldocs to an empty list
        patparser.xmldocs = []
        # Reset xmliteration to 0
        patparser.xmliteration = 0
        fulldoc = ''
        try:
            fulldoc = get_xml(pageurl, urls[i])
        except zipfile.BadZipfile:
            print 'Found bad zip file, attempting to redownload'
            fulldoc = get_xml(pageurl, urls[i], True)
        
        # Check for patent-application-publication (will help me narrow down when it changes)
        
        try:
            f = open(getwd() + download_directory + '.breakpoint', 'w')
            f.write('')
            f.close()
            patparser.split_xml(fulldoc)
        except KeyboardInterrupt:
            f = open(getwd() + download_directory + '.breakpoint', 'w')
            f.write(getUrlFilename(urls[i]))
            f.close()
            print 'Wrote \'%s\' to %s' % (getUrlFilename(urls[i]), f)
            sys.exit(1)

        
        global scraping
        scraping = True
        patparser.scrape_multi()
        
        file_writer.write_data(patparser.datalists)
        # If Control+C was pressed during scrape, then exit
        if break_scrape:
            sys.exit(1)

        scraping = False

        i+= 1
        # DB - For debugging, break at a certain point
        break 

# Get zip file and unzip, setting fulldoc to a value
def get_xml(pageurl, url, forcedl=False):
    tempzip = getwd() + download_directory + getUrlFilename(url)
    if os.path.isfile(tempzip) and not forcedl:
        print 'Found', getUrlFilename(url), 'on disk, not downloading.'
        response = tempzip
    else:
        print 'Downloading', url, 'from server.'
        response = (urllib.urlretrieve(url, tempzip, reporthook))[0]
        print '\n'
    print 'Got response:', '\'' + response + '\''
    
    fulldoc = None
    with zipfile.ZipFile(response, 'r') as myzip:
        xmlname = getUrlFilename(url, True) + '.xml'
        # Patent application xml is not always in root, namelist() gets all files within zip
        for filename in myzip.namelist():
            print filename
            if getUrlFilename(filename) == xmlname:
                print 'Found %s in %s' % (xmlname, response)
                fulldoc = myzip.open(filename)

    return fulldoc


# Get working directory
def getwd():
    return os.path.dirname(os.path.realpath(__file__))


def getUrlFilename(url, remftype=False):
    # Gets the string from the last / character to the end (for example http://patents.reedtech.com/.../ipa140213.zip would return ipa140213.zip
    return url[url.rfind('/') + 1: url.rfind('.') if remftype else len(url)]


# Remove any already downloaded zips from the download list
def removeDownloaded(urls):
    remove = []
    forceinclude = ''

    # Try to get the filename of a breakpoint
    try:
        f = open(getwd() + download_directory + '.breakpoint')
        
        # Get string on first line
        for line in f:
            forceinclude = line
            break
    except IOError:
        pass

    for url in urls:
        for f in os.listdir(getwd() + download_directory[:-1]):
            if f == getUrlFilename(url) and f != forceinclude:
                # Check for bad/incomplete files
                try:
                    zipfile.ZipFile(getwd() + download_directory + f, 'r')
                    remove.append(url)
                    #print 'Removed %s as it was already downloaded' % getUrlFilename(url)
                except zipfile.BadZipfile:
                    #print '\n' + f, 'is a bad zip file, not removing from dl list.'
                    pass

    [urls.remove(url) for url in remove]
    return len(remove)

        
# Split the date of the filename into yy, mm, dd.  Optionally call getUrlFilename on the string
def splitDate(url, convertName=False):
    datearr = []
    if convertName:
        url = getUrlFilename(url, True)
    
    date = re.sub('[^0-9]', '', url)
    if len(date) == 6:
        # Iterate 0, 2, 4, getting substrings [0,2],[2,4],[4,6].  Python does some pretty cool stuff
        for i in xrange(0, len(date), 2):
            #print 'date[%d : %d]' % (i, i+2)
            datearr.append(date[i : i + 2])
    else:
        raise Exception('Date string had length %d, expected 6' % len(date))
    
    return datearr
 

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
    sys.stdout.write("\rProgress: %d%%, %.2f %.2f MB, %d KB/s, %d seconds passed" % (percent, float(progress_size) / (1024 * 1024), float(total_size) / (1024 * 1024), speed, duration))
    sys.stdout.flush()


class CSVFileWriter():

    datalist = []

    def getCSV(self, mode='w'):
        f = open(getwd() + '/output.csv', mode)
        return f


    def write_output(self, f, output_str):
        # If line doesn't already have line break at end, add one
        if len(output_str) > 0 and output_str[-1] != '\n':
            f.write(output_str + '\n')
        else:
            f.write(output_str)


    def setup_datalist(self, datalist):
        for i in xrange(0, len(datalist)):
            data = re.sub('\n+', ' ', datalist[i][1]).strip()

            datalist[i][1] = data
        return datalist


    def clear_file(self):
        f = self.getCSV()
        f.write('')
        f.close()


    def write_data(self, datalists):
        count = 0
        #f = open(os.path.dirname(os.path.realpath(__file__)) + '/output.csv', 'a') 
        f = self.getCSV('a')

        for datalist in datalists:
            if datalist != None:
                datalist = self.setup_datalist(datalist) 
                
                tempdatalist = []
                [tempdatalist.append(data[1]) for data in datalist]

                output = ', '.join(tempdatalist)
                #print output
                self.write_output(f=f, output_str=output)
                #write_output(f=f, output_str='-')
            count += 1

        f.close()


def safe_exit(signum, frame):
    # Reset original signal handler
    signal.signal(signal.SIGINT, original_sigint)
    
    if scraping:
        print 'Program is currently scraping; will exit once done.'
        global break_scrape
        break_scrape = True
    else:
        # Make Ctrl+C behave normally if not scraping
        raise KeyboardInterrupt()


if __name__ == '__main__':
    start = time.clock()

    # Catch Control + C so that you cannot exit during a scrape
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, safe_exit)
    
    file_writer = CSVFileWriter()
    patparser.bindFileWriter(file_writer)

    main()
    elapsed = (time.clock() - start)
    print '\nTime elapsed:', elapsed

import urllib
import os
import re
import time
import sys
import signal
import zipfile

import patutil
import patparser

# For safely exiting after a scrape, not during it
scraping = False
break_scrape = False

download_directory = '/temp/'

file_writer = None 

def main():
    # Clear csv file
    file_writer.clear_file()
    file_writer.write_header(patparser.tagList)

    # Get patent urls from webpage
    pageurl = 'https://www.google.com/googlebooks/uspto-patents-applications-text.html'
    print 'Getting webpage', pageurl + '...',
    urls = []

    # Remove any xml file from earlier than 2007
    for url in patparser.getUrlList(pageurl):
        if int(patutil.splitDate(url, True)[0]) >= 7:
            urls.append(url)
    #urls = ['pa010531.zip']
    
    numremoved = 0#removeDownloaded(urls)
    print 'Found %d urls (%d removed because they were already downloaded)' % (len(urls), numremoved)
    if not os.path.exists(patutil.getwd() + download_directory):
        os.makedirs(patutil.getwd() + download_directory)
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
            f = open(patutil.getwd() + download_directory + '.breakpoint', 'w')
            f.write('')
            f.close()
            patparser.split_xml(fulldoc)
        except KeyboardInterrupt:
            f = open(patutil.getwd() + download_directory + '.breakpoint', 'w')
            f.write(patutil.getUrlFilename(urls[i]))
            f.close()
            print 'Wrote \'%s\' to %s' % (patutil.getUrlFilename(urls[i]), f)
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
    tempzip = patutil.getwd() + download_directory + patutil.getUrlFilename(url)
    if os.path.isfile(tempzip) and not forcedl:
        print 'Found', patutil.getUrlFilename(url), 'on disk, not downloading.'
        response = tempzip
    else:
        print 'Downloading', url, 'from server.'
        response = (urllib.urlretrieve(url, tempzip, reporthook))[0]
        print '\n'
    print 'Got response:', '\'' + response + '\''
    
    fulldoc = None
    with zipfile.ZipFile(response, 'r') as myzip:
        xmlname = patutil.getUrlFilename(url, True) + '.xml'
        # Patent application xml is not always in root, namelist() gets all files within zip
        for filename in myzip.namelist():
            print filename
            if patutil.getUrlFilename(filename) == xmlname:
                print 'Found %s in %s' % (xmlname, response)
                fulldoc = myzip.open(filename)

    return fulldoc



# Remove any already downloaded zips from the download list
def removeDownloaded(urls):
    remove = []
    forceinclude = ''

    # Try to get the filename of a breakpoint
    try:
        f = open(patutil.getwd() + download_directory + '.breakpoint')
        
        # Get string on first line
        for line in f:
            forceinclude = line
            break
    except IOError:
        pass

    for url in urls:
        for f in os.listdir(patutil.getwd() + download_directory[:-1]):
            if f == patutil.getUrlFilename(url) and f != forceinclude:
                # Check for bad/incomplete files
                try:
                    zipfile.ZipFile(patutil.getwd() + download_directory + f, 'r')
                    remove.append(url)
                    #print 'Removed %s as it was already downloaded' % patutil.getUrlFilename(url)
                except zipfile.BadZipfile:
                    #print '\n' + f, 'is a bad zip file, not removing from dl list.'
                    pass

    [urls.remove(url) for url in remove]
    return len(remove)
 

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
    
    file_writer = patutil.CSVFileWriter()

    main()
    elapsed = (time.clock() - start)
    print '\nTime elapsed:', elapsed

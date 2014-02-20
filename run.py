import urllib
import os
import re
import time
import sys
import zipfile
import patparser

cleanupMode = 0 # Cleanup mode for files: 0 is none, 1 will remove all extracted directory trees, and 2 will remove the directory trees and their zip files

def main():
    # Clear csv file
    clear_file()
    pageurl = 'http://patents.reedtech.com/'
    print 'Getting webpage', pageurl + '...',
    # Get patent urls from webpage
    urls = patparser.getUrlList(pageurl + 'parbft.php')
    print 'Done.'
    #urls = [['/pa010315.zip', 'emulate', '.']]
    if not os.path.exists(getwd() + '/temp/'):
        os.makedirs(getwd() + '/temp/')
    i = len(urls) - 1
    # Iterate through urls from oldest to newest, downloading and parsing each one
    while i >= 0:
        # Reset xmldocs to an empty list
        patparser.xmldocs = []
        # Reset xmliteration to 0
        patparser.xmliteration = 0
        fulldoc = ''
        try:
            fulldoc = get_xml(pageurl, urls[i])
        except zipfile.BadZipfile:
            print 'Found bad zip file, attempting to redownload'
            time.sleep(0.5)
            fulldoc = get_xml(pageurl, urls[i], True)
        patparser.split_xml(fulldoc)
        patparser.scrape_multi()
        
        i-= 1
        # DB - For debugging, break after one iter
        if i < len(urls) - 15:
            print 'Break at i=%s' % i
            break


# Get zip file and unzip, setting fulldoc to a value
def get_xml(pageurl, url, forcedl=False):
    tempzip = getwd() + '/temp/' + getUrlFilename(url[0])
    if os.path.isfile(tempzip) and not forcedl:
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
                print 'Found %s in %s' % (xmlname, response)
                fulldoc = myzip.open(filename)

    return fulldoc


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
    sys.stdout.write("\rProgress: %d%%, %.2f %.2f MB, %d KB/s, %d seconds passed" % (percent, float(progress_size) / (1024 * 1024), float(total_size) / (1024 * 1024), speed, duration))
    sys.stdout.flush()


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

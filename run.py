import urllib
import os
import re
import time
import sys
import signal
import zipfile

import patutil
import patparser

download_directory = '/temp/'
file_writer = None 

def main():
    filename = patutil.cmd_args['filename'] 
    ptype = patutil.cmd_args['ptype']
    pageurl = None

    if ptype == 'a':
        pageurl = 'https://www.google.com/googlebooks/uspto-patents-applications-text.html'
    elif ptype == 'g':
        pageurl = 'https://www.google.com/googlebooks/uspto-patents-grants-text.html'
        
    urls = []

    if filename == None:
        print 'Getting webpage', str(pageurl) + '...',
        # Get patent applications and remove any xml file from earlier than 2007
        for url in patparser.getUrlList(pageurl, ptype):
            if patutil.splitDate(url, True)[0] >= 7:
                urls.append(url)

        numremoved = removeParsed(urls, file_writer.getCSVsInDir())
        print 'Found %d urls (%d removed because they already had CSV files)' % (len(urls), numremoved)
    else:
        urls = [filename]
    
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
        # Ugly way to get single files to work, assumes urls has one element which is the filename
        if filename == None:
            try:
                fulldoc = get_xml(pageurl, urls[i])
            except zipfile.BadZipfile:
                print 'Found bad zip file, attempting to redownload'
                fulldoc = get_xml(pageurl, urls[i], True)
        else:
            if urls[i][-4:] == '.xml':
                fulldoc = open(patutil.getwd() + urls[i])
            else: print 'Not a top priority, will do later.' # TODO

        # Split and scrape xml
        year = patutil.splitDate(urls[i], True)[0] 
        patparser.tags.setTags(year)
        file_writer.setParser(patparser)
        patparser.split_xml(fulldoc, patutil.cmd_args['max_iter'])
        patparser.scrape_multi(year, patutil.cmd_args['no_nsf_flag'])
        
        # Setup csv for writing
        file_writer.setFilename(patutil.getUrlFilename(urls[i], True))
        file_writer.clear_file()
        file_writer.write_header(patparser.tags.getHeadings())

        file_writer.write_data(patparser.datalists)

        i+= 1
        if patutil.cmd_args['single_doc_flag']:
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


def removeParsed(urls, csvs):
    remove = []
    for url in urls:
        for csv in csvs:
            # Compare names of csvs to names of urls, and remove matching ones
            if patutil.getUrlFilename(csv) == patutil.getUrlFilename(url, True) + '.csv':
               remove.append(url)

    #print urls
    #print remove
    [urls.remove(url) for url in remove]
    return len(remove)

# Remove any already downloaded zips from the download list
# (Obsolete, removeParsed should be used instead)
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
    patutil.print_over("\rProgress: %d%%, %.2f %.2f MB, %d KB/s, %d seconds passed" % (percent, float(progress_size) / (1024 * 1024), float(total_size) / (1024 * 1024), speed, duration))


if __name__ == '__main__':
    start = time.clock()
    
    args = sys.argv
    
    patutil.cmd_args['filename'] = None if args[1][0] == '-' else args[1]

    # Setup flags
    for i in xrange(0,len(args)):
        if args[i] == '-g' or args[i] == '-a': # Get whether to find patent grants or applications
            patutil.cmd_args['ptype'] = args[i][1:]
        elif args[i] == '-maxsplit': # Set a max number to split (useful for debug)
            patutil.cmd_args['max_iter'] = int(args[i+1])
        elif args[i] == '-maxnsf':
            patutil.cmd_args['max_nsf'] = int(args[i+1])
        elif args[i] == '-nonsf': # Find all data, not just nsf
            patutil.cmd_args['no_nsf_flag'] = True
        elif args[i] == '-single': # Prevents downloading and/or parsing of more than one xml file
            patutil.cmd_args['single_doc_flag'] = True
        elif args[i] == '-dump':
            patutil.cmd_args['dump_flag'] = True

    print 'Straight args: %s, ptype %s, max_iter %s, max_nsf %s, filename %s, nonsf %s, single_doc %s' % (args, patutil.cmd_args['ptype'], str(patutil.cmd_args['max_iter']), str(patutil.cmd_args['max_nsf']), str(patutil.cmd_args['filename']), str(patutil.cmd_args['no_nsf_flag']), str(patutil.cmd_args['single_doc_flag']))

    filename = patutil.getUrlFilename(patutil.cmd_args['filename'])
    if filename != None and patutil.cmd_args['ptype'] == None:
        if filename[:3] == 'ipa':
            patutil.cmd_args['ptype'] = 'a'
        elif filename[:3] == 'ipg':
            patutil.cmd_args['ptype'] = 'g'

    file_writer = patutil.CSVFileWriter()
    main()
     
    elapsed = (time.clock() - start)
    print '\nTime elapsed: %s seconds' % elapsed

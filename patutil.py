import os
import re
import codecs

# Get working directory
def getwd():
    return os.path.dirname(os.path.realpath(__file__))

# Gets the string from the last / character to the end (for example http://patents.reedtech.com/.../ipa140213.zip would return ipa140213.zip
def getUrlFilename(url, remftype=False):
    return url[url.rfind('/') + 1: url.rfind('.') if remftype else len(url)]


# Split the date of the filename into yy, mm, dd.  Optionally call getUrlFilename on the string
def splitDate(url, makeint=False):
    datearr = []
    url = getUrlFilename(url, True)
    
    date = re.sub('[^0-9]', '', url)
    if len(date) == 6:
        # Iterate 0, 2, 4, getting substrings [0,2],[2,4],[4,6].  Python does some pretty cool stuff
        for i in xrange(0, len(date), 2):
            #print 'date[%d : %d]' % (i, i+2)
            dateslice = date[i : i + 2]
            if makeint: dateslice = int(dateslice)
            datearr.append(dateslice)
    else:
        raise Exception('Date string had length %d, expected 6' % len(date))
    
    return datearr


class CSVFileWriter():

    datalist = []

    def getCSV(self, mode='w'):
        f = codecs.open(getwd() + '/output.csv', mode, 'utf-8-sig')
        return f

    def write_header(self, tagList):
        f = self.getCSV()
        f.write(','.join(tagList))
        f.write('\n')
        f.close()

    def write_output(self, f, output_str):
        # If line doesn't already have line break at end, add one
        if len(output_str) > 0 and output_str[-1] != '\n':
            f.write(output_str + '\n')
        else:
            f.write(output_str)


    def setup_datalist(self, datalist):
        for i in xrange(0, len(datalist)):
            print 'datalist[%s][1] = %s' % (i, datalist[i]) 
            # remove newline characters (need to remove \r as well for some reason)
            data = re.sub('[\r,\n+]', '', datalist[i][1]).strip()
            # Arbitrary placeholder for comma in text
            data = re.sub(',', '\u0238', data)
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

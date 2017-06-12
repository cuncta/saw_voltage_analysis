#!/usr/bin/env python

"""
module for the READING of spec files

saving is done by a single function, which writes a column data into spec file.
This is NOT in the SpecFile class
I could actually put it into the class, but all the function would do is to write in the file and 
update the SpecFile class.

Now this is kind of total rewrite of the specscan thingy, 
I introduce a class specfile. until noe specfile was only 
a set of scans, large and slow. For large scans, it needed to 
reread the whiole file, and this took minutes (10kilolines)

funcions use seek-tell to get fast to the position for reding.

for old comments and for old interface use: 
import specscan_c
this delivers a list of columns

Ivo Zizak

This is not written to write the files properly,
it is just for extracting the most data
from the scan.
It reads also comments and tries to intuitively
interpret user variables too.

      TODO: read MCA inline
TODO: Saving must be implemented in class.
When it is installed as a function, it has to check the number of
scans in the file every time it adds the fscan, this measn: indexing the 
file every time!

how would the class look like:

class specfile
      ColumnData file header (or some dictionary)

      ColumnData scan[]

      looong integer index[] - index of the scans in the file for update
      number of scans is than length

      timestamp read
      timestamp file

      rescan (scan the files for scans)

      load (load all scans)

      ADDITIONAL DATA!!!
      images, CCD, XRF....
      
        
"""



__author__ = "Ivo Zizak (ivo.zizak@bessy.de)"
__version__ = "$ 0.70 $"
__date__ = "$Date: 2017/01/30 00:00:00 $"
__copyright__ = "Copyright (c) 2007-2017 Ivo Zizak"
__license__ = "Python"

import os
import string
from ColumnData import *
import numpy as np

class SpecFile:
    def __init__(self, filename):
        self.filename=filename

        # this is filled at init
        self.file_header={}

        # for indexing and some scan information
        self.N_scans = 0
        self.index = []       # position in file where the #S line starts
        self.data_index = []  # position in file where the first data line starts
        self.scan_title = []  # title for the reference (if no title, set it to command)
        self.scan_no = []     # scan number as spec enumerates it
        self.N_lines = []     # number of lines in scan
        self.N_mca  = []     # number of mca detectors
        self.scan_com = []    # command issued for scan

        # from file header
        self.axisnames = []   # I need the list of axes to put it in ColumnData when returning
        self.counters = []    # complicated: all variables and columns which are not axes

        # file change tracking: for is_uptodate()
        self.index_epoch = 0
        self.update_epoch = 0
        self.file_size = 0

        self.DEBUG = 1 # useless

        # spec file options
        self.doublespaces = 1

        # check that the file exist
        # open the file
        try:
            fp = open(self.filename,"rb")
        except:
            return None

        Scannum = 0
        context = 0
        strip=re.compile("^#\S+\s")
        unspace=re.compile("\s+")
        startspaces=re.compile("^\s*")
        chop=re.compile("\s*(\r|\n)$")
        collapse_spaces=re.compile("\s\s+")

        self.index_epoch = time.time()
        line=fp.readline()

        inscan = 1

        print "Reading Header"
        print line
        self.file_header["file_epoch"]=0 # default value
        while line!="" and inscan==1: # set here something like While scan not over or ""
            line=startspaces.sub("",line)
            line=chop.sub("",line)
            if re.match("^#",line):
                if re.match("^#\s*F",line):
                    self.file_header["file_name"]=chop.sub("",strip.sub("",line))
                    
                if re.match("^#\s*E",line):
                    self.file_header["file_epoch"]=chop.sub("",strip.sub("",line))

                if re.match("^#\s*D",line):
                    self.file_header["Date"]=chop.sub("",strip.sub("",line))

                if re.match("^#\s*O",line):
                    # names of motor axes
                    #print "axes names, FIXME"
                    #print " there is a good way to strip spaces at the start and at the end"
                    
                    if self.doublespaces:
                        linet=collapse_spaces.sub("  ",line[3:])
                        names = linet.split("  ")
                    else:
                        linet=collapse_spaces.sub(" ",line[3:])
                        names = linet.split(" ")
                    
                    for name in names:
                        uname = re.match("^\s*(\S.*\S)|\S\s*$",name)
                        if uname:
                            if uname.group(1):
                                self.axisnames.append(string.replace(uname.group(1)," ","_"))
                    # this was easy, but I have to think about how to
                    # correlate the P-lines with this
                    # print axisnames

                line=fp.readline()
                if re.match("^#\s*S",line):
                    inscan = 0

        # remember time of last opening
        del line
        fp.close()

        # index the scans
        self.index_file()
        print "real numbering",self.scan_no 
        # close the file
        return

    def index_file(self, start=0): # I didnt decide yet what do I count, lines or bytes
        #print "INDEXING START"
        strip=re.compile("^#\S+\s")
        unspace=re.compile("\s+")
        startspaces=re.compile("^\s*")
        chop=re.compile("\s*(\r|\n)$")
        collapse_spaces=re.compile("\s\s+")
        # open the file,
        Scannum = 0
        context = 0
        try:
            fp = open(self.filename,"rb")
        except:
            return None

        # if start is larger than the scan number, start at scan number
        # check also the size of the index list
        # if the size of the index list or scan_N are 0, start at 0
        
        # index = 0: first scan

        if len(self.index) != 0 or self.N_scans!=0:
            if start<self.N_scans:
                fp.seek(self.index[start-1])  # Go to the start of the PREVIOUS scan
                dummy=fp.readline()           # assures that we don't reread the last scan
                #if self.DEBUG print "READING line a
                context = 1 # in header
                index = start-2
            else:
                start = 0
                index = -1
        else:
            start = 0
            index = -1
            
        #All I need now is to measure where the header is, and where the data
        #I could also measure how many data lines are there,
        # and detect if there are any MCA lines
        position=fp.tell()    

        multiline = 0

        # this is an iterator, it reads all lines and it is not possible to
        # get the tell(), because the file is first rad, and than the loop is started, i.e. when I 
        # run the loop over the first line, the complete file is already scanned.
        # for line in fp.readlines():   # Py2.2 -> "for line in fp:"

        position=fp.tell()
        line=fp.readline()

        while line!="":
           
            line=startspaces.sub("",line)
            line=chop.sub("",line)
            #if re.match("^\s*$",line): # skip empty lines:
            #    multiline = 0
            #else: 
            if len(line)>0 and multiline == 0:
                #if re.match("^#",line):
                if line[0]=="#":
                    if re.match("^#\s*S",line):
                        context=1
                        index = index+1
                        # found NEW header
                        # increase size of all pointer list size first
                        self.N_scans=self.N_scans+1
                        self.index.append(position)
                        self.data_index.append(0)
                        self.scan_title.append((' '.join(chop.sub("",strip.sub("",line)).split(" ")[1:])).strip())
                        self.scan_no.append(chop.sub("",strip.sub("",line)).split(" ")[0])
                        self.N_lines.append(0)
                        self.N_mca.append(0)
                        self.scan_com.append((' '.join(chop.sub("",strip.sub("",line)).split(" ")[1:])).strip())
                    if re.match("^#\s*L",line):
                        if self.doublespaces:
                            names =  strip.sub("",line).split("  ")
                        else:
                            names= strip.sub("",line).split(" ")
                        for name in names:
                            uname = re.match("^\s*(\S.*\S|\S)\s*$",name)
                            if uname:
                                #print uname.group(1)
                                newname=string.replace(uname.group(1)," ","_")
                                # first check if it is in axes:
                                try:
                                    r = self.axisnames.index(newname)
                                except:
                                    try:
                                        r = self.counters.index(newname)
                                    except:
                                        self.counters.append(string.replace(uname.group(1)," ","_"))

                else:
                    if context == 1:
                        context = 2
                        self.data_index[index]=position # I dont use this actually

                    if not re.match("^@",line):
                        #print "index", index
                        #print "N_lines",self.N_lines
                        self.N_lines[index] = self.N_lines[index] + 1 # this is also not very useful
                    else:
                        # this is the first MCA line, get the detector name (ABCD...)
                        # look how many detectors we have
                        # here I should only count the @A occurances
                        if re.match("^@A",line):
                            self.N_mca[index] = self.N_mca[index] + 1 
                        
            # if line ends with \\, the new line is the continuation of this line and should not be read or counted
            multiline=0
            try:
                if (line[-1]=="\\"):
                    multiline = 1
            except:
                pass

            position=fp.tell()
            line = fp.readline()
        
        # scan it for the lines of the type #S
        # remember position of the scan start in the file
        # maybe I'll need some data to remember, but in the first version 
        # I'll skip it.
        # I should remember all the data defined in previous scans
        # in comment lines.
        # get the number of lines in scans, titles and commands
        fp.close()
        #print "INDEXING END"

    def get_scan( self, SCAN_N, start=0, end=None , getmca=0, lineno=0):
        # getmca changes the functionality of this function: not the whole scan but only the mca associated daa is goig to be returned
        # this reads the scan and returns the column data
        # going to the scan is done fast, without reading, 
        # starting to read directly from the line where we stopped
        # start and end can be used for reading only part of the scan,
        # skipping is a problem because of MCA, I'll have to read everything
        # even if the scan has a million points, and it does notpay to remember where which line starts.
        # Since the files always grow, 
        # so we can be much faster.
        strip=re.compile("^#\S+\s")
        unspace=re.compile("\s+")
        startspaces=re.compile("^\s*")
        chop=re.compile("\s*(\r|\n)$")
        collapse_spaces=re.compile("\s\s+")
        # open the file,

        context = 1 # I beam myself up into the #S-line, and change context only once when the header ends.
        
        # first check if the required data exist

        # create return object
        scan=ColumnData()        
        # Now skip to the start of the scan and start reading header
        # we do this until the first character of the line is not # any more
        # than we read data
        # we put everything into a ColumnData thingy and return it
        # we dont touch MCA data
        fp = open(self.filename)
        # move the pointer to the start of the header
        # read scan
        #print "INDEX"
        #print self.index
        #print "real numbering",self.scan_no #
        
        fp.seek(self.index[SCAN_N])
        
        # start reading, the first line should be the #S-line
        try:
            scan.set_variable("File_Date",self.file_header["Date"])
        except:
            pass
        scan.set_variable("File_Epoch",self.file_header["file_epoch"])
        scan.set_variable("File_Name",self.file_header["file_name"])
        scan.set_variable("scan_ord_number", SCAN_N )
        scan.set_variable("scan_number",self.scan_no[SCAN_N])
        scan.set_variable("scan_command",self.scan_com[SCAN_N])
        scan.title=self.scan_com[SCAN_N]
        scan.axes = self.axisnames
        #print "scan.axes",scan.axes
        
        # I should have diferent loops for header and data, so I can skip header when rereading the data.
        # All I have to remember (once per file)
        # which was a last scan and last data line that was read, and at which position in file it started
        # than I can start from there.
        # but I would have to trust the caller function. It would be complicated to read a part of the scan

        position=fp.tell()    
        #print "position", position
        multiline = 0

        position=fp.tell()
        line=fp.readline()

        inscan = 1
        axisvalues = []
        columnlabels = []
        sylvionames = []
        sylviovalues = []
        mcadata={}
        
        #print "Reading scan", SCAN_N
        #print "first line:",line
        while line!="" and inscan==1: # set here something like While scan not over or "" # this would break at stop/resume, because it adds an empty line

            line=startspaces.sub("",line)
            line=chop.sub("",line)
            if re.match("^\s*$",line): # skip empty lines: problem, empty lines contain sometimes spaces
                multiline = 0
            else:
                thismultiline=0
                if re.match(r".*\\",line):
                    thismultiline = 1
                
                # DO THE WHOLE THING HERE
                # first in header, than in data, skip MCA lines, there is get_MCA function
                #header
                # some header variables are already scanned by indexing function
                # but they are stil in SpecFile structure
                # we should construct the ColumnData struture "scan" here

                # we need from header:  name, date, eventually found variables, and column names
                # from SpecFile structure we need the axis names, filename, file epoch...
                
                #if re.match("^#",line): # HEADER
                if line[0]=="#": # HEADER                  
                    if re.match("^#\s*D",line):
                        # original date
                        scan.set_variable("Date",chop.sub("",strip.sub("",line)))

                    if re.match("^#\s*P",line):
                        # axes positions at the beginning of the scan
                        # names of motor axes
                        #print "axes values FIX REGEX"
                        names= line.split(" ")
                        for name in names[1:]:
                            uname = re.match("^\s*(\S+)\s*$",name)
                            if uname:
                                axisvalues.append(uname.group(1))

                    if re.match("^#\s*L",line):
                        # column labels
                        #print "column labels"
                        #print strip.sub("",line)
                        if self.doublespaces:
                            names =  strip.sub("",line).split("  ")
                        else:
                            names= strip.sub("",line).split(" ")
                        for name in names:
                            uname = re.match("^\s*(\S.*\S|\S)\s*$",name)
                            if uname:
                                #print uname.group(1)
                                newname=string.replace(uname.group(1)," ","_")
                                try:
                                    r = columnlabels.index(newname)
                                except:
                                    columnlabels.append(string.replace(uname.group(1)," ","_"))

                    #####################################################################
                    # variables in comments

                    if re.match("^#\s*(U|C)",line):
                        # comment: I evaluate this too
                        # I'm looking for occurences of (\s\S+\s*=\s*\S*\s)
                        # I don't know how many of those are there
                        #print "FOUND COMMENTED VARIABLE"
                        #print line
                        equ = re.compile("(\S+)\s*=\s*(\S+)(\s|$)")
                        occ=0
                        for i in  equ.findall(strip.sub("",line)):
                            #print ":",i
                            scan.set_variable(i[0],i[1])
                            occ=occ+1
                            #print table1
                        # what if the thing is an array?
                        # if I found only one "=" try to read the array
                        if occ==1:
                            #print line
                            equ = re.compile("=\s*(.+)$")
                            varname=i[0]
                            i = equ.findall(startspaces.sub("",strip.sub("",chop.sub("",line))))
                            #print "-%s-"%startspaces.sub("",strip.sub("",chop.sub("",line)))
                            if i:
                                #save the string 
                                # BUG: i is a list of 1: do something with it
                                # i is list now, and should not be added as a list
                                # this would confuse the ColumnData, because this is than registered as a column
                                scan.set_variable(varname,string.join(i," "))

                    
                    ########################################################################
                    # Sylvio Haas special!
                    # no spaces in names here !
                    if re.match("^#\s*C(\w)L\s",line):
                        # labels for variables
                        #print "Sylvio labels FIX REGEX"
                        names= line.split(" ")
                        for name in names[1:]:
                            uname = re.match("^\s*(\S+)|\S\s*$",name)
                            #print name
                            if uname:
                                sylvionames.append(uname.group(1))

                    if re.match("^#\s*C(\w)V\s",line):
                        #values for Sylvio special
                        #print "Sylvio values FIX REGEX"
                        names= line.split(" ")
                        for name in names[1:]:
                            uname = re.match("^\s*(\S+)\s*$",name)
                            #print name
                            if uname:
                                sylviovalues.append(uname.group(1))
                    
                    if(getmca > 0):
                        if re.match("^#@MCA\s*",line):
                            #values reading the format for MCA files
                            print "Format for MCA", line

                        if re.match("^#@CHANN\s",line):
                            #values reading the format for MCA files
                            print "Channel numbers", line

                        if re.match("^#@CALIB\s*C(\w)V\s",line):
                            #values reading the format for MCA files
                            print "Calibration", line
                            

                    #########################################################################

                else:
                    if getmca == 0:
                        if multiline == 0 and  not re.match("^@",line): # not reading MCA data
                            if context == 1: #first line, header is over: fill the data read from header
                                for i in range(0,len(scan.axes)) :
                                    scan.set_variable(self.axisnames[i], axisvalues[i])
                                for i in range(0,len(sylviovalues)) :
                                    scan.set_variable(sylvionames[i], sylviovalues[i])
                                #print "Column Labels"
                                #print columnlabels
                                context = 2
                            # continuing to read the first line
                            # for every column make a list, by every line append values to the list,
                            # at the end send lists to ColumnData
                            line=unspace.sub(" ",line)
                            #print chop.sub("",line).split(" ")
                            # this works too, but is not very fast!
                            scan.add_row(columnlabels,chop.sub("",line).split(" "))
                    
                    # read the mca data if the getmca parameter id OK
                    
                    if getmca > 0 and scan.lines == lineno:
                        if multiline == 0 :
                            if re.match("^@A",line):
                                print "getting the MCA", scan.lines
                                # first copy all the header from the scan into MCA
                                # except the data.
                                
                                #NO; better, keep the scan, just replace the data with the channels!
                                mca = scan.copy()    # this copies only the pointer
                                
                                # than add all the current data from the line, if any into the header.
                                # NO, I have already the scan, why should I copy the data...
                                mca.print_s()
                                #for label in columnlabels,chop.sub("",line).split(" ")
                            # now this is for all the detecors:
                            if re.match("^@",line):
                                # This is the first occurance of the detector, so it does not exist yet 
                                # since we read the COLUMNN we know how many data are in the spectrum
                                
                                # get the leter of the detector:
                                mcaname = line[1] # we hope to get it right
                                if re.match(r".*\\",line):              # matches the closing \
                                    line = re.sub(r"\\\n"," ",line)
                                    line = re.sub(r"\\"," ",line)
                                    line = re.sub(r"\s+"," ",line)
                                    line = re.sub(r"\s+$","",line)
                                    line = re.sub(r"^\s+","",line)
                                    #print line
                                    #print "continuing ", mcaname
                                    context=3
                                mcaline = line[3:]
                        else: # we are in multiline
                            #print ">>>",context,"   ",line
                            if (context==3):
                                if re.match(r".*\\",line):
                                    line = re.sub(r"\\\n"," ",line)
                                    line = re.sub(r"\\"," ",line)
                                    line = re.sub(r"\s+"," ",line)
                                    line = re.sub(r"\s+$","",line)
                                    line = re.sub(r"^\s+","",line)
                                    mcaline = mcaline+" "+line
                                    #print "continuing ", mcaname
                                    context=3
                                else:
                                    try:
                                        line = re.sub(r"\n","",line)
                                    except:
                                        pass
                                    context=2
                                    line = re.sub(r"\s+"," ",line)
                                    line = re.sub(r"\s+$","",line)
                                    line = re.sub(r"^\s+","",line)
                                    mcaline = mcaline+" "+line
                                    mcadata[mcaname] = mcaline.split(" ")
                                    print "LEN", len(mcadata[mcaname])
                                    #mcalist.append(mcadata)
                                    mcanumdata=np.array(mcadata[mcaname])
                                    #print mcanumdata.shape
                                    #print "AAAA"
                                    # the following was to insure that the variable gets the number value ad not the string:
                                    #for i in range(len(mcadata[mcaname])):
                                        #print mcaname, i, mcanumdata[i], mcadata[mcaname][i]
                                        #mcanumdata[i] = float(mcadata[mcaname][i])
                                    
                                    mca.set_variable(mcaname,mcanumdata.astype(float))
                                    

                multiline=0
                if thismultiline==1:
                    multiline=1
                    

            position=fp.tell()
            line = fp.readline()
            if re.match("^#\s*S",line):
                inscan = 0    # we found the next scan

        # EXIT
        fp.close()
        if getmca==0 :
            return scan
        else: 
            return mca

    def get_scan_num( self, scanno, start=0, end=None ):
        # this gets te scan according to the spec scan number
        # the ames are in index, 
        print "real numbering",self.scan_no 
        # now compare the content with the given number, and the one which matches is ou scan number.
        print "searching for the scan number",scanno
        ord=0
        for scan_no in self.scan_no:
            if int(scan_no)==int(scanno):
                print "it is the scan number",ord
                return self.get_scan(ord , start, end)
            ord=ord+1


    def get_MCA( self, SCAN_N=0, getmca=1, line=0 ):
        # default values are to be set so that they can load ingle spectrm from mca file with default parameterrs
        # this returns the column data structure where all the motor positions and detector values are in header
        # in the data block we have only the spectrum, size is N_chanels
        # in case we have several detectors, the return file will have several columns.
        # column Energy is filled from calibration if there is one found in the file
        
        # strategy: first get the scan
        mca = self.get_scan(SCAN_N=SCAN_N, getmca=1, lineno = line)

        return mca
        pass

    def is_uptodate(self):
        # this compares the date and size of the file to saved values
        # If they are same, 1 is returned. If file changed, 0 is returned
        return 0
    def update(self):
        if (self.is_uptodate()):
            return
        self.index_file()

# here for compatibility, old function:
# open a file get all scans, put them in a list, and return list
# could be good for evaluation
def LoadSpecFile(filename):
    spec = SpecFile(filename)
    
    pass

# convert all peculiarities into normal spec user defined variables
# the command takes a filename and a scanlist as argument
def SaveSpecFile(filename, specscan, overwrite=0):
    print "saving ",filename
    #check if the file exists
    if(overwrite==1):
        try:
            os.remove(filename)
        except:
            pass
    nums=0
    # if it does not, we have to write a file header
    if(os.path.exists(filename)):
        TEMPSCAN=SpecFile(filename)
        nums=TEMPSCAN.N_scans
        TEMPFILE = open(filename,"a")
        # find the last scan! the enumeration does not work
        # properly, just like in spec
    else:
        TEMPFILE = open(filename,"w")
        # file header
        TEMPFILE.write("#F %s \n"%filename)
        TEMPFILE.write("#E %d \n"%int(time.time()))
        TEMPFILE.write("#D %s "%time.ctime())
        # write some motor coordinates here
        # go over all scans and extract teh variables and columns
        # get axes later, I don't want to save detectors here
        
        # write axis names here in #O fields, in groups
        # I'll have to rely that all the scans have same axes, so I'll 
        # construct the axis names from the first scan
        o_line=1
        axis_nr = 0
        for axis in specscan.axes:
            if( int(axis_nr/8)==axis_nr/8.0):
                TEMPFILE.write("\n#O%d "%o_line)
                o_line=o_line+1
            TEMPFILE.write("  %8s"%axis)
            axis_nr=axis_nr+1
        TEMPFILE.write("\n")
    TEMPFILE.write("\n")

    
    # specscan is the list of columns.
    num=1
    a = specscan
    #scan header
    TEMPFILE.write("#S %d %s \n"%(nums+num, a.title))
    TEMPFILE.write("#D %s "%time.ctime())

    # write axes here in #P fields, in groups
    # problems: some axes are columns of the scan: write the first line then
    o_line=1
    axis_nr = 0
    for axis in a.axes:
        if( int(axis_nr/8)==axis_nr/8.0):
            TEMPFILE.write("\n#P%d "%o_line)
            o_line=o_line+1
        # now check if the axis is constant:
        try: 
            r = a.variables.index(axis)
            TEMPFILE.write("  %8g"%a.data[axis][0])
        except:
            TEMPFILE.write("  %8g"%a.data[axis])
        axis_nr=axis_nr+1
    TEMPFILE.write("\n")
    

    for i in a.variables:
        #print i, type(a.data[i])
        #print i, a.data[i].shape
        # dangerous: I have arrays as elements now
        if len(a.data[i].shape)==0:
            # do this only if a variable is not an axis
            if a.data[i].dtype.kind=="S":
                #if type(a.data[i])==types.StringType:
                
                TEMPFILE.write("#U %s = %s\n"%(i,a.data[i]))
            else:
                #print i , a.data[i], type(a.data[i])
                TEMPFILE.write("#U %s = %g\n"%(i,a.data[i]))


    #for i in a.axes:
    #    TEMPFILE.write("#C axis %s \n"%i)
    # now the columns

    TEMPFILE.write( "#N %d\n"%len(a.labels))
    TEMPFILE.write( "#L ")
    for i in a.labels:
        TEMPFILE.write( " %s "%i)
    TEMPFILE.write( "\n")

    #print "lines : ", a.lines
    #print "dim : ", a.dim
    #print "size : ", a.size

    if a.dim>0:
        for n in range(0, a.size[0]):
            #print n
            for i in a.labels:
                if type(a.data[i][n])==types.StringType:
                    TEMPFILE.write(" \"%s\" " % a.data[i][n])
                else:
                    TEMPFILE.write(" %g "%a.data[i][n])
            TEMPFILE.write( "\n")
    TEMPFILE.write( "\n")
    num=num+1
        
    

############################################
#
#       MCA
#      save and read MCA files
#
###########################################
# WARNING: this is directly transported from another version, check!
#

def SaveSpecMCAFile (filename, table, overwrite=0):
    if(overwrite==1):
        try:
            os.remove(filename)
        except:
            pass
    nums=0
    # if it does not, we have to write a file header
    if(os.path.exists(filename)):
        TEMPSCAN=SpecFile(filename)
        nums=len(TEMPSCAN)
        TEMPFILE = open(filename,"a")
        # find the last scan! the enumeration does not work
        # properly, just like in spec
    else:
        TEMPFILE = open(filename,"w")
        # file header
        TEMPFILE.write("#F %s \n"%filename)
        TEMPFILE.write("#D %s \n\n"%time.ctime())
        # write some motor coordinates here
        # go over all scans and extract teh variables and columns
        # get axes later, I don't want to save detectors here
        TEMPFILE.write("\n")
    # now the MCA header
        TEMPFILE.write("#S 1 mca \n")
        #TEMPFILE.write("#S %d %s \n"%(nums+num, a.data["scan_command"]))
        TEMPFILE.write("#D %s \n"%time.ctime())
        
        # important: we have to analyse the energy axis to get the calibration!
        # I assume that the axis is linear
        calib=[0,1,0]
        # I also assume that the column holding energy is called "Energy"
        calib[0]=table.data["Energy"][0]
        calib[1]=table.data["Energy"][1]-table.data["Energy"][0]
        TEMPFILE.write("#@MCA %16C\n")
        TEMPFILE.write("#@CHANN %i %i %i %i\n"%(table.lines, 0,table.lines, 1 ))
        TEMPFILE.write("#@CTIME 1 1 0\n") # I lie here!
        TEMPFILE.write("#@CALIB %f %f %f\n"%(calib[0],calib[1],calib[2]))
    # now write the columns, 
    colnum=0
    mcalabels="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for col in table.labels:
        if col=="Energy":
            pass
        else:
            TEMPFILE.write("@")
            TEMPFILE.write(mcalabels[colnum])
            # now in series of 16
            chan=0
            a=table.get_column(col)
            while chan<table.lines:
                TEMPFILE.write(" %g"%a[chan])
                if 16*int((chan+1)/16) == chan+1:
                    if chan<table.lines-1:
                        TEMPFILE.write("\\\n")
                    else :
                        TEMPFILE.write("\n")
                chan=chan+1
            colnum=colnum+1
    TEMPFILE.close()



#######################################################################################################################
#
#   test

if __name__ == "__main__":
    print "test for the spec file read function"
    print "be sure that you have some spec file"
    print "give the path to it as argument"

    # opening and reading the file 
    spec=SpecFile(sys.argv[1])

    print "before loading individual scans:"

    print "number of scans %d"%spec.N_scans
    print "axes : ", spec.axisnames
    print "counters : ", spec.counters

    

    for i in range(0,spec.N_scans):
        a = spec.get_scan(i)
        print
        print "scan", a.data["scan_number"]
        print "Title:", a.title
        print "#S", int(a.data["scan_ord_number"]), a.data["scan_command"]
        print "date", a.data["Date"]
        print "axes", a.axes
        print "KEYS", a.data.keys()
        #a.labels.sort()
        print "LABELS", a.labels
        print "VARIABLES", a.variables
        print "dimension", a.dim
        print "lines", a.size
        #a.print_s()
        #print
        #print "contents of Monitor"
        #print a.get_column("Monitor")
    
        #for l in a.variables:
            #print l,"=",a.data[l]

        # SAVING TEST:
        if(i==0):
            SaveSpecFile("testscpecfile_6.spec",a,1)
        if(0<i<10):
            SaveSpecFile("testscpecfile_6.spec",a,0)

    # it is hard to test the updating feature, one should simulate the measurement
    # and read teh file during the writing.... later

    print "\n\n\n"
    
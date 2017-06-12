#!/usr/bin/env python

"""
version 2009.03-27

module for the manipulation of spec files

Ivo Zizak

This is not written to write the files properly,
it is just for extracting the most data
from the scan.
It reads also comments and tries to intuitively
interpret user variables too.

Although I would like to use the same structure for other files,
there are some very peculiar solutions in spec file format:
- It is possible to have a space in axis name. Although
  it would be normal to put such names in parethesis or in qoutes
  Gerry uses _two_spaces_ as delimiter for the names, and a single
  space in the numeric rows.
  Way out: make a test for the line with names and decide if we use
  one or two spaces as delimiter make an internal variable which
  describes the result of the test
- two scans with same number can exist in the file
  way out: use the order number in file to enummerate scans
  for more complex searces use any variable to select the scan
  like sample_name=back or command=mesh ... later

Main interface:
input: filename, scan number, line number
return values: dictionary with values

help functions:
get the number of scans in file,
check the uniqueness of scan names (numbers)

change log:
0.01: Translation from tcl function
      Get_Line_From_Spec_File
      from my texture evaluation script
      and the construction of the python class
      main program which prints some statistics from given spec file

0.02: function 'getline' is very practical if we are doing some line-for-line
      evaluation, but sometimes (for plot or fit) I would like to extract the complete collumn
      The first version could call the getline function  and fill a list or a touple.
      ...
      AB OVO

0.03: all scan thingys moved into the new class ColumnData. The specfile function is going to open the file,
      read it, close it, and return a list of ColumnData instances.
      Over and out.

      It would be wrong to write the read_spec_file as a method for ColumnData.
      The problem is that the single spec file contains several scans, and is actually a list of scans.
      Additional problem is that it is not structured. If there is a line in scan3 header telling us that
      the absorber is 5, this still applies on the scan 5, because nobody changed absorber since  than.

      Thet's why spec file is a new class. It should be possible to write a spec file from a list of
      scans and some aditional information (We have to know which variables are axes, and which are the scalers...)

      Now about implementation:
      I actually don't need a class, I need a function.

      I was using sets! In ColumnData I didn't use them. sets are not very well implemented in python.
      There are different implementations in different versions of python. At the time of writing this,
      the actual version 2.4 moves the set functions from sets module into the base module. The implementations are
      also diferent. Names change Version 1.5 uses 'set', 2.4 uses 'Set' for aparently the same thing...
       Set is not very usable for columns. I have to know which axes ar in the set, but I don't want to 
       lose the order, so it is better to use lists ot even num arrays (arrays can't be changed).

2009-03-27
      a kind of Save function. looks good, newplot can read the most of it, I can reread it


TODO:

      UPDATING :
      I need a class!, because there is much more data we need for reentrant functions. However:
      REENTRANT READING OF SEQUENTIAL DATA   COLIDES WITH   OO !!!!!!!!!!!!
      And maybe with other things. I'll probably have to reread the whole file.

      I can't have both!
      so in the first version, I just whant a function which reads the spec file and returns the list of scans
      BUG: the columns still get mixed up! I would like to keep the order
      TODO: read MCA inline
        
"""



__author__ = "Ivo Zizak (ivo.zizak@bessy.de)"
__version__ = "$ 0.03 $"
__date__ = "$Date: 2007/01/30 00:00:00 $"
__copyright__ = "Copyright (c) 2007 Ivo Zizak"
__license__ = "Python"

import os
from ColumnData import *

def SpecFile(filename):
    scanlist=[]
    table1={}
    axisnames=[]
    sylvionames=[]
    doublespaces=1
    context=0
    
    #some reguler expressions used later
    strip=re.compile("^#\S+\s")
    unspace=re.compile("\s+")
    startspaces=re.compile("^\s*")
    chop=re.compile("\s*(\r|\n)$")
    collapse_spaces=re.compile("\s\s+")

    # open the file
    try:
        fp = open(filename,"r")
        Scannum=0
        for line in fp.readlines():   # Py2.2 -> "for line in fp:"
            line=startspaces.sub("",line)
            # here we have the line!
            # is this a comment?
            if re.match("^#",line):
                if re.match("^#\s*F",line):
                    # original filename
                    table1["file_name"]=chop.sub("",strip.sub("",line))

                if re.match("^#\s*E",line):
                    # original epoch
                    table1["file_epoch"]=chop.sub("",strip.sub("",line))

                if re.match("^#\s*D",line):
                    # original date
                    table1["Date"]=chop.sub("",strip.sub("",line))

                if re.match("^#\s*O",line):
                    # names of motor axes
                    #print "axes names, FIXME"
                    #print " there is a good way to strip spaces at the start and at the end"
                    
                    if doublespaces:
                        linet=collapse_spaces.sub("  ",line[3:])
                        names= linet.split("  ")
                    else:
                        linet=collapse_spaces.sub(" ",line[3:])
                        names= linet.split(" ")
                    
                    for name in names:
                        uname = re.match("^\s*(\S.*\S)|\S\s*$",name)
                        if uname:
                            axisnames.append(string.replace(uname.group(1)," ","_"))
                    # this was easy, but I have to think about how to
                    # correlate the P-lines with this
                    # print axisnames

                if re.match("^#\s*S",line):
                    # start of the scan header
                    #print line,
                    if context==2:
                        # there was already one scan
                        #scan.print_s()
                        # stupid cscan makes empty lines in the middle of the scan
                        #print "end of scan!"
                        #context=0
                        scanlist.append(scan)
                        scan.axes=axisnames
                        #print "end of scan"
                        #scan.print_s()
                    axisvalues=[]
                    sylviovalues=[]
                    sylvionames=[]
                    columnlabels=[]
                    #curscan=curscan+1
                    scanline=0
                    context=1
                    #starting a new scan here
                    Scannum=Scannum+1
                    scan=ColumnData();
                    table1["scan_number"]=chop.sub("",strip.sub("",line)).split(" ")[0]
                    table1["scan_ord_number"]=Scannum
                    table1["scan_command"]=(' '.join(chop.sub("",strip.sub("",line)).split(" ")[1:])).strip()
                    #print table1["scan_command"]

                #if re.match("^#\s*G",line):
                    # transformation matrix (does not mean much
                    # print "G"
                    # continue

                #if re.match("^#\s*Q",line):
                    # ?
                    #print "Q"
                    #continue

                if re.match("^#\s*P",line):
                    # axes positions at the beginning of the scan
                    # names of motor axes
                    #print "axes values FIX REGEX"
                    names= line.split(" ")
                    for name in names[1:]:
                        uname = re.match("^\s*(\S+)\s*$",name)
                        if uname:
                            axisvalues.append(uname.group(1))

                #if re.match("^\s*X",line):
                    # set temperature
                    #print "SetTemp"

                #if re.match("^\s*N",line):
                    # number of columns
                    # I actually don't need this here
                    # it is irrelevant how many variables are defined in columns, and how many in header
                    #continue

                if re.match("^#\s*L",line):
                    # column labels
                    #print "column labels"
                    #print strip.sub("",line)
                    if doublespaces:
                        names =  strip.sub("",line).split("  ")
                    else:
                        names= strip.sub("",line).split(" ")
                    for name in names:
                        uname = re.match("^\s*(\S.*\S|\S)\s*$",name)
                        if uname:
                            #print uname.group(1)
                            columnlabels.append(string.replace(uname.group(1)," ","_"))
                    #this was easy, but I have to think about how to
                    # correlate the P-lines with this
                    #print columnlabels

                if re.match("^#\s*(U|C)",line):
                    # comment: I evaluate this too
                    # I'm looking for occurences of (\s\S+\s*=\s*\S*\s)
                    # I don't know how many of those are there
                    equ = re.compile("(\S+)\s*=\s*(\S+)\s")
                    occ=0
                    for i in  equ.findall(strip.sub("",line)):
                        #print ":",i
                        table1.update({i[0]:i[1]})
                        occ=occ+1
                        #print table1
                    #what if the thing is an array?
                    # if I found only one "="
                    if occ==1:
                        #print line
                        equ = re.compile("=\s*(.+)$")
                        varname=i[0]
                        i = equ.findall(startspaces.sub("",strip.sub("",chop.sub("",line))))
                        #print "-%s-"%startspaces.sub("",strip.sub("",chop.sub("",line)))
                        if i:
                            #save the string 
                            table1.update({varname:i[0]})
                            # I tried to analyse the string and get the array, but it is too complicated
                            #print i[0]
                            #values=i[0].split(",")
                            #if len(values)==1:
                                #print "no komma"
                                # I have to change this!!!
                            #    values=i[0].split(" ")
                            #if len(values)!=1:
                            #    print table1["scan_number"],varname,values
                            #    table1.update({varname:values})
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

                #########################################################################

                
                #if re.match("^\s*R",line):
                    # comment: I dont know what to do with this
                    # print "results, neglet"
                    #continue

                #END of #-block
            else:
                if re.match("^\s*$",line):
                    if context==2:
                        #scan.print_s()
                        # stupid cscan makes empty lines in the middle of the scan
                        # so I can't do this here
                        #print "end of scan!"
                        #context=0
                        #scanlist.append(scan)
                        #print "end of scan"
                        #scan.print_s()
                        pass
        
                # if nothing of these matched, I'll try to interpret it as data
                else:
                    # axes positions at the beginning of the scan
                    if context==1:
                        #print "reading data: "
                        context=2
                        #we just switchced from header to values, sort coordinates here
                        #for a in table1.keys():
                        #    print "setting", a
                        #    scan.set_variable(a,table1[a])
                        table1.update(dict(zip(axisnames,axisvalues)))
                        table1.update(dict(zip(sylvionames,sylviovalues)))
                        for a in table1.keys():
                            #print "setting", a
                            # NOW, update variables, only if theye are not labels!
                            update=1
                            for i in columnlabels:
                                #print "comparing",a,"and",i
                                if a==i:
                                    update=0
                            if update==1:
                                scan.set_variable(a,table1[a])
                            #else:
                                #print "not updating"
                        #print table1

                    # get the line
                    # numbers are delimited with several spaces!
#                   strip=re.compile("^#\S+\s")
                    if re.match("^@",line):
                        # we are in mca thingy
                        if re.match("\$",line):
                            # this is not the last line:
                            context=3
                        else:
                            context=2
                        # where do I put these things???
                        # separately of the variables and columns I should
                        # add a mca container. For many mca columns
                    line=unspace.sub(" ",line)
                    # as soon as I "dict" it, it mixes up everything!
                    table1.update(dict(zip(columnlabels,chop.sub("",line).split(" "))))
                    scan.add_row(dict(zip(columnlabels,chop.sub("",line).split(" "))))
                    scan.labels=columnlabels;
                    #print columnlabels
                    #print columnlabels[0]
                    #print chop.sub("",line).split(" ")
                    #(dict(zip(columnlabels,chop.sub("",line).split(" "))))
                           # foundit=0

            
            
        # if the file ends in the middle of the scan, append it
        #scan.print_s()
        if context==2:
        #    #print "end of scan!"
            context=0
        #    for a in table1.keys():
        #        scan.set_variable(a,table1[a])
            #scan.title = scan.data["title"]
            scanlist.append(scan)
            scan.axes=axisnames
            #print "end of scan and file"
        #scan.print_s()

        del line                      # Cleanup transient variable
        fp.close()
    except IOError:
        # do something on error
        pass

    #print scanlist[52]
    return scanlist

# here save spec file
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

    
    # specscan is the list of columns.
    num=1
    for a in specscan:
        #scan header
        #TEMPFILE.write("#S %d %s \n"%(nums+num, a.title))
        TEMPFILE.write("#S %d %s \n"%(nums+num, a.data["title"]))
        #TEMPFILE.write("#S %d %s \n"%(nums+num, a.data["scan_command"]))
        TEMPFILE.write("#D %s \n"%time.ctime())
        for i in a.variables:
            if type(a.data[i])==types.StringType:
                TEMPFILE.write("#U %s = %s\n"%(i,a.data[i]))
            else:
                TEMPFILE.write("#U %s = %g\n"%(i,a.data[i]))
                
            
        #for i in a.axes:
        #    TEMPFILE.write("#C axis %s \n"%i)
        # now the columns
        
        TEMPFILE.write( "#N %d\n"%len(a.labels))
        TEMPFILE.write( "#L ")
        for i in a.labels:
            TEMPFILE.write( " %s "%i)
        TEMPFILE.write( "\n")

        for n in range(0, a.lines):
            for i in a.labels:
                if type(a.data[i][n])==types.StringType:
                    TEMPFILE.write(" \"%s\" " % a.data[i][n])
                else:
                    TEMPFILE.write(" %g "%a.data[i][n])
            TEMPFILE.write( "\n")
        TEMPFILE.write( "\n")
        num=num+1
        
        
#######################################################################################################################
#
#   test

if __name__ == "__main__":
    print "test for the spec file read function"
    print "be sure that you have some spec file"
    print "give the path to it as argument"


    # opening and reading the file 
    spec=SpecFile(sys.argv[1])

    print len(spec)

    for a in spec:
        print
        print "scan", int(a.data["scan_number"])
        print "Title:", a.title
        print "#S", int(a.data["scan_ord_number"]), a.data["scan_command"]
        print "date", a.data["Date"]
        print "KEYS", a.data.keys()
        #a.labels.sort()
        print "LABELS", a.labels
        print "VARIABLES", a.variables
        print "lines", a.lines
        #a.print_s()
        #print
        #print "contents of Monitor"
        #print a.get_column("Monitor")
    
        #for l in a.variables:
            #print l,"=",a.data[l]
        

    SaveSpecFile("testscpecfile.spec",spec)
    

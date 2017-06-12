#!/usr/bin/env  python
# this defines several commands for easy file manipulation
# mkdir, CopyDirTree, iterator for find file,
# ini-file manipulation (my format, have to change it)

# iterator defines global variable framename,
# can't be easily put in a module, have to make a class of it...

import os, os.path
import sys
import re
import string
import math

def mkdir(dirname):
    if os.path.exists(dirname):
        if os.path.isdir(dirname)==0:
            print dirname, " is not directory!, exiting"
            exit
    else :
        print "creating ", dirname
        os.makedirs(dirname)

# In teh original tcl version there are also
#    FindFile
#    MakeTree
# but they don't do anything inteligent.

def CopyDirTree(fromrootdir, torootdir):
    mkdir(todir)
    start=1
    directories = []
    while ((start==1) | (len(directories)>0)): # this is a walker, it will go into subdirs!
        if start==0:
            directory=directories.pop()
            fromdir=os.path.join(fromrootdir,directory)
            topdir=os.path.join(torootdir,directory)
        else:
            directory=""
            fromdir=fromrootdir
            todir=torootdir
            start=0
            
        #print "found dir ", framedir
        mkdir(todir)
        for name in os.listdir(framedir):
            fullpath = os.path.join(framedir,name)
            if os.path.isdir(fullpath):
                directories.append(os.path.join(directory,name))  # It's a directory, store it.


    
# now the file reading of our complicated ini file
# change to real ini file to be compatible with framelib 5

def Get_Next_Peak(file, b):
    a={}
    block=0
    while (block==0):      
        line=file.readline()
        if line=="":
            return 0
        #chomp line
        if line.endswith("\n"):
            line=line[0:-1]
        # selections here
        m=re.match('peak\s*=\s*(.*)$',line)
        if m: a["peak"] = m.group(1)
            
        m=re.match('chi_d\s*=\s*(.*)$',line)
        if m: a["chi_d"] = m.group(1)
            
        m=re.match('tth\s*=\s*(.*)$',line)
        if m: a["tth"] = m.group(1)
            
        m=re.match('back1\s*=\s*(.*)$',line)
        if m: a["back1"] = m.group(1)

        m=re.match('back_low\s*=\s*(.*)$',line)
        if m: a["back1"] = m.group(1)

        m=re.match('back2\s*=\s*(.*)$',line)
        if m: a["back2"] = m.group(1)
 
        m=re.match('back_high\s*=\s*(.*)$',line)
        if m: a["back2"] = m.group(1)
            
        m=re.match('resolution\s*=\s*(.*)$',line)
        if m: a["resolution"] = m.group(1)
            

        if re.match("^end",line):
            block=1
            b.update(a)
            print "peak structure",b
    return 1
    
    

def Get_Next_Measurement(file, b):
    a={}
    block=0
    while (block==0):      
        line=file.readline()
        if line=="":
            return 0
        #chomp line
        if line.endswith("\n"):
            line=line[0:-1]
        # selections here
        m=re.match('tx\s*=\s*(.*)$',line)
        if m: a["tx"] = m.group(1)
            
        m=re.match('file\s*=\s*(.*)$',line)
        if m: a["file"] = m.group(1)
            
        m=re.match('scans\s*=\s*(.*)$',line)
        if m: a["scans"] = m.group(1)
                    
        if re.match("^end",line):
            block=1
            b.update(a)
    return 1


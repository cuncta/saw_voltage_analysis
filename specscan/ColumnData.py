#!/usr/bin/env python

"""
multicolumn data is going to have it's own class.

class ColumnData

Despite the name, this is a container for multicolumn data.
except the multicolumns it can save also some constant variables,
expand variables into columns, and perform some operations on columns.
For this last thing, the columns should be NumArrays.
In the first implementation, I'm using lists. Let's start simple.

NumPy version!
        
"""

__author__ = "Ivo Zizak (ivo.zizak@bessy.de)"
__version__ = "$ 0.02 $"
__date__ = "$Date: 2007/01/30 00:00:00 $"
__copyright__ = "Copyright (c) 2007 Ivo Zizak"
__license__ = "Python"


import sys, re, time, string, types
#import sets
# new in this version: I use arrays instead of lists
from numpy import *

class ColumnDataError(Exception):pass

class ColumnData:
    """
    class ColumnData
    contains multicolumn data + variables
    
    """
    def __init__ (self):
        # here we try to differ between columns and variables.
        # Why is this important? Variables are just replacements for constant columns!
        self.labels=[]
        # it is also important that we are able to enummerate columns
        # variables are all data.keys which are no is not a labels
        self.variables=[]
        # self.axes is a list of axes. There are axes and measured values.
        # this is not important for evaluation, but sometimes it
        # is neccessary to know which values are on ordinate, and
        # which on abscisse. This list must be set from outside.
        # axes can contain even the names which are not defined as
        # variables or columns
        self.axes=[]
        # values is actually everything which is not axis, so I
        # won't define it until really neccessary
        # self.values[]

        # introducing multidimensional arrays
        self.dim=0
        self.size=()
        # old size convention, it is maybe better to reuse it instead of
        # tuple. Problem, if there is no data, than size is empty touple.
        self.lines=0
        #data storage, contains arrays or scallars
        self.data={}
        # just for saving, maybe introduce header structure
        self.title=""

    def copy (self):
        """
        makes a copy of the instance,
        example: CD1 is defined, CD2 not yet:
        CD2 = CD1.copy()
        now is CD2 copy of CD1, not the pointer to the same instance
        """
        newthing=ColumnData()
        newthing.labels.extend(self.labels)
        newthing.variables.extend(self.variables)
        newthing.title=self.title
        newthing.lines=self.lines
        newthing.axes=self.axes
        newthing.data=self.data.copy()
        newthing.dim=self.dim
        newthing.size=self.size
 

        return newthing

    def __repr__(self):
        """
        representation class
        """
        return repr(self.data)

    def print_s(self):
        """
        prints in a spec-style the
        ColumnDat
        this is not 100% compatible to spec, but can be read from
        some programs like xplot and newplot
        """
        print "#S%s" % self.title
        for a in self.variables:
            if type(self.data[a])==types.StringType:
                print "#U %s = \"%s\"" % (a, self.data[a])
            else:
                print "#U",a,"=",self.data[a]

        for a in self.axes:
            print "#C axis",a,"\n"
            
        print "#N",len(self.labels)
        print "#L",
        for a in self.labels:
            print a,
        print

        if self.dim==1:
            for n in range(0, self.size[0]):
                for a in self.labels:
                    #print type(self.data[a][n])
                    #print self.data[a].dtype.kind
                    #print dtype('string')
                    if self.data[a].dtype.kind=="S":
                        print "\"%s\"" % self.data[a][n],
                    else:
                        print self.data[a][n],
                print
            print

    def set_value(self, name, value):
        # this ia to be used instead of set variable
        # set variable can send the whole vector of variables at once, problem:
        # I can't have vector variables
        # Using the set_value, it would be possible to have vector variables,
        # scallar columns, and vector columns. Vector columns are used for MCA
        # I would have to increase the dimension of the "Column" or to have a
        #  new descriptor for each column, which is going to give me the dimensionality
        # of the element
        pass
    
    def set_variable(self, name, value):
        """
        set_variable adds a variable OR a column in the ColumnDat structure

        All numerical types and strings can be added.
        If a single value is sent, a variable is created,
        if a list or tuple is sent, a column is created.
        Tuples are internally converted to list.
        It is not allowed to mix numbers and strings in one column.
        Most errors raise an exception. (mixing types, wrong column length...)
        Columns have to be of the same length.

        adding numpy functionality:

        leave all type conciderations back to numpy

        mixing data types is dealed with in numpy:
        diferences: if I mix text and numbers, everything is converted in text
        
        """
        #print "DON'T USE set_variable; USE set_value !!!"
        
        # try to evaluate strings 

        # convert the new value in numarray
        try:
            ar = array(float(value))
        except:
            ar = array(value)

        #check if the array has a uniquie data type
        if ar.dtype == dtype("object"):
            raise ColumnDataError, "mixing objects into columns"
        
        if len(ar.shape)==1 :
            if len(self.size)==0 :
                self.size=ar.shape
                self.dim=len(self.size)
            if ar.shape != self.size :
                # it is an array of the wrong size
                raise ColumnDataError, "wrong size of new element"
                return 0
        # I am trying to put the 2D array as a column of vector data!
        if len(ar.shape)==2 :
            # I have got a 2D array
            if len(self.size)==0 :
                self.size=(ar.shape[0],)
                # the ColumnData stays dim1
                self.dim=len(self.size)
            if (ar.shape[0],) != self.size :
                raise ColumnDataError, "wrong size of new element"
                return 0
                

        self.delete(name)
        #print "variables", self.variables
        if len(ar.shape)==0 :
            self.variables.append(name)
        else:
            #print self.labels
            #self.labels.append(name)
            self.labels=append(self.labels,name)
        
        # if data already exist, delete it!

        self.data[name]=ar
        
        #print type(self.data)
        
    def delete(self, name):
        """
        this deletes a variable or column.
        Argument: variable name
        """
        # this should delete the variable or the label and make nop diference
        
        try:
            self.labels.remove(name)
        except: pass
        try:
            self.variables.remove(name)
        except: pass
        try:
            del self.data[name]
        except:
            pass

    
    def get_row (self,lineno=1):
        """
        returns one row of the data structure as dictionary.
        Dictionary has the form:
        {{variable_name:value}...}
        It does not make difference if the variable is defined as column
        or as a constant. Dictionary contains all variables and
        i-th row of the columns.

        The function is made for row-row evaluations, so it is
        irrelevant if some variable changed during the scan, or if
        it is constant. We get the value.
        """
        # make a new dictionary which we are giong to return
        # keys are labels, values are values...

        #what we actually have to do is to copy data, and to
        # replace all columns with the n-th row

        #dangerous! this copies the pointer!
        #edata=self.data
        # this does not work properly: it should return columns AND variables!
        # this returns a LIST: the point is that columns can have different data types, arrays not
        # better: this returns a dictionary"
        if self.dim!=1:
            raise ColumnDataError, "get_row does not work on multidimensional or zero-dimmensional data"
            return None
        
        edata=self.data.copy()
        #print "dimension",self.dim
        #print "labels",self.labels
        
        # problem: 
        for a in self.labels:
            edata[a]=self.data[a][lineno-1]
        
        return edata

    def get_column (self,a):
        """
        This returns a column of data as an array!. This function does not
        make any difference between constants and columnar values, i.e.
        if the argument is a name of a constant, a list is returned
        with the length of the number of rows, filled with constant value
        this is made for plots which can plot anything against anything.
        To find out which variables are columns, access the ColumnData.labels
        """
        try:
            t=self.labels.index(a)
            # ok the thing is a column
            # print "is a column",a
            return(self.data[a])
        except:
            # print "is a label",a
            # thing is a variable
            # need to construct a list of N values of
            # the variable
            # returning array!
            li=self.data[a]+zeros(self.size)
            print "is a label",a
            print "size ", self.size
            print "returning ", li
            return(li)
        raise ColumnDataError, "unexisting column"
        return None
        
    def variable_repr (self, name, lineno):
        data=self.data[name][lineno-1]
        # we have data, now I have to print it

        if data.dtype.kind=="S":
            print "STRING", data
            return "%s" % data
        else:
            return "%s" % data.__repr__()
      
        #if self.dim==1:
        #    for n in range(0, self.size[0]):
        #        for a in self.labels:
        #            #print type(self.data[a][n])
        #            #print self.data[a].dtype.kind
        #            #print dtype('string')
        #            if self.data[a].dtype.kind=="S":
        #                print "\"%s\"" % self.data[a][n],
        #            else:
        #                print self.data[a][n],
        #        print
        #    print
            
    def eval (self, expression):
        # the idea is to perform the calculation using column and variable names
        # and the expression in string.
        # I won't parse the string and call EQ, I'll rather transform the string
        # so the python can evaluate it.
        pass
    
    
    def add_row (self,labels, values):
        """
        this should be used only internally, but since I'm not sure yet,
        it is still public.
        This function adds the last row to all columns.
        This can be used when we sequentially read a file on the disc
        to avoid saving data on other places temporarilly.
        This is also practical if we are measuring scans,
        than we can simply add new measurements at the end.
        The order of the data in the list must be the same as the order of the
        labels in ColumnData.labels.

        problem! I use numeric, the size is immutable! 

        this function can work as before only if I reallocate the data for every added row!

        problem, this works only for 1-dim data!
        
        """
        # I get the dictionary with data
        # I have to see how many row do I have
        if self.dim>1:
            print "2"
            raise ColumnDataError, "add_row does not work on multidimensional or zero-dimmensional data"

       # if labels==[]:
       #     return()
       #     raise ColumnDataError, "get_row does not work on multidimensional or zero-dimmensional data"


        #print "self.labels",self.labels
        #print "labels",labels

        #special case, we don't have any columns yet
        if self.dim==0:
            self.dim=1
            self.labels=copy(labels)
            #self.labels=labels
            for lab in range(0,size(self.labels)) :
                try:
                    newval=float(values[lab])
                except:
                    newval=values[lab]
                self.data[labels[lab]]=array((newval,))
                self.size=(1,)
                #print "added",self.data[labels[lab]]
                self.lines=1
            return
            
        # now get the dictionary keys, compare it with labels and report error
        if len(self.labels)!=len(labels) :
            print "3"
            raise ColumnDataError, "mismatching number of columns"
            
        # now for every thing in labels check if it has new value
        if (self.labels!=labels).all():
            print self
            print labels
            raise ColumnDataError, "column name mismatch"
            
        # i could check for type, but it is not the error!
        # if I have a numeric column and get string
        # the whole column is converted into strings

        # now make a copy of the column in a list, append the value and
        # put it back into array.
        for lab in range(0,size(self.labels)) :
            #print "before",self.data[lab]
            try:
                newval=float(values[lab])
            except:
                newval=values[lab]
            self.data[labels[lab]]=concatenate((self.data[labels[lab]].copy(),resize(array(newval),(1,))))
            self.size=self.data[labels[lab]].shape
            #print "after",self.data[lab]
            self.lines=self.size[0]
        
        

#######################################################################################################################
#
#   test

if __name__ == "__main__":
    print "test for the ColumnData Class"
    scan=ColumnData()
    print type(scan)
    scan.set_variable("test", 1)
    scan.set_variable("teststring", "1")

    print scan.__doc__

    print scan


    scan.set_variable("tes", [1,2,3] )

    try:
        scan.set_variable("tep", [1,2] )
    except:
        print "got the exception for mixing column lengths"

    try:
        scan.set_variable("tep", [1,2, "tere"] )
    except:
        print "got the exception for mixing data types"

    
    try:
        scan.set_variable("tep", [1,2, {1:2,2:3,3:4}] )
    except:
        print "got the exception for unsupported data format"

    # this should go through without exception (1.7 is float, 2 is integer!)
    scan.set_variable("Y", [1.7,2,3] )

    scan.set_variable("touple", (1.5,6,9) )
    scan.print_s()

    a=scan.get_row(2) # this returns a dictionary of the values in the 3rd row and variables.
    print "row 3 of data ",a

    print "column -> variable"

    scan.set_variable("touple", 3 )
    scan.print_s()
    print "saving ban here"
    ban=scan.copy()
    print "this is ban"
    ban.print_s()
    


    print "variable -> column"
    scan.set_variable("touple", (0,8,3) )
    scan.title=scan.title+"1"
    scan.print_s()


    print "string variable"
    scan.set_variable("touple", "filename" )
    scan.print_s()

    print "string array"
    scan.set_variable("touple", ("a","rea","oko" ))
    scan.print_s()
    print "string array"


    # deleting variables
    print "deleting Y"
    scan.delete("Y")
    scan.delete("X")
    scan.print_s()

    print "string array"
    scan.set_variable("Y", (1 ,2 ,12.4))
    scan.print_s()

    # getting columns
    a= scan.get_column("Y")

    print "getting collumn Y:",a
    
    # adding rows
    # trick: has to know how many columns are there.
    # we should also know what is in these rows!
    # however, this function is not very nice.
    # now I know that there are 3
    scan.delete("tep")
    t=len(scan.labels)
    print "there are ",t,"columns"
    #leave this to numeric:
    #a=range(0,t)+1*12.41



    o={"tes":12 , "touple":"nos", "Y":-2.9e14}
    print "add_row",o

    try:
        scan.add_row(o.keys(),o.values())
    except:
        print "got exception "

    o={"tes":12 , "touple":"nos", "Y":"string!!!"}
    print "add_row",o
    try:
        scan.add_row(o.keys(),o.values())
    except:
        print "got exceprion"
    scan.print_s()
    o={"tes":12 , "touple":"nos", "DS":"string!!!"}
    #This is going to add teh
    # first value in the first column, the second in the second..
    # how do I know which is first?
    # The order is like in scan.labels
    print "add_row",o
    try:
        scan.add_row(o.keys(),o.values())
    except:
        print "got exceprion"
    # it could be possible to add the complete row like a dictionary, but it is too complicated...
    # don't like it
    scan.print_s()

    print "size", scan.size
    print "lines", scan.size[0]

    tran=ColumnData()
    tran.set_variable("DS",12)
    tran.print_s()
    print "column overrides the variable type!"
    tran.add_row(o.keys(),o.values())
    tran.print_s()

    # copying complete datasets
    print "retrieving backup"
    ban.print_s()

    #try to do some calculations with our set:
    # at this point I have numerical columns 'tes' and 'Y'
    # let us just try newc=tes*sin(Y)
    ban.set_variable("newc", ban.data["tes"]*sin(ban.data["Y"]) )
    ban.set_variable("sum", ban.data["tes"]+ban.data["Y"] )

    #works!
    
    ban.print_s()

    # combining two datasets
    
    # collapsing columns int mean values

    # now we have 'tople' column:
    # overwrite it with a variable:
    
    # test tuple, tuple has no index method!
    #convert tuples to lists!
    #print scan

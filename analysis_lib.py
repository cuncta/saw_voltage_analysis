import numpy as np
import matplotlib.pyplot as plt
import scipy.integrate as integrate
import time
from scipy import asarray as ar,exp
from scipy.signal import argrelextrema
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit
from pyPdf import PdfFileWriter, PdfFileReader



#from PIL import Image



def get_matrix_from_tiff(dir,pic_name,y_pixel,background):
	'''this function read a stack of tif files and extract the values of certain pixels through
	the stack and saves them in a nice matrix
	
	dir = 'directory of the files (name of the files has to be changed in the functionn
		for the moment)'
	pic_name = 'the name of the tif image without the number'
	
	first_im = number of the first image to analyze
	
	n_stack = number of stacks(number of scans)
	
	xpix_in = initial pixel for loop on x coordinate
	xpix_fin = final pixel for loop on x coordinate
	
	ypix_in = initial pixel for loop on y coordinate
	ypix_fin = final pixel for loop on y coordinate
	
	fin = lenght of a delay scan(or how many images for each scan)
	'''
	

	#background

	bg = np.asarray(Image.open(dir + background+'.tif').convert('L'))
	
	fin = 4
	for i in range(0,5):
		num = str(29 + i)
		#print 'num', num
		#print 'n_stack', n_stack
		#print 'num', num
		im = Image.open(dir + pic_name+num+'_0001.tif')
		#pix = im.load()
		pix = np.asarray(Image.open(dir + pic_name+num+'_0001.tif').convert('L'))
		#background removal
		#pix = pix - bg
		try:
			intensity
		except NameError:
			#print "running for the first time"
			intensity = pix[:,y_pixel]
			intensity = intensity.reshape(1004,1)
			#print 'intensity', intensity.shape

		else:
			#print "running for the", i+1, " time"
			int = pix[:,y_pixel]
			int = int.reshape(1004,1)			
			intensity = np.concatenate((intensity, int), axis=1)

	
	return intensity
def tiff_read_and_extract(dir,pic_name, first_im,n_stack, xpix_in, xpix_fin, ypix_in, ypix_fin, fin):
	'''this function read a stack of tif files and extract the values of certain pixels through
	the stack and saves them in a nice matrix
	
	dir = 'directory of the files (name of the files has to be changed in the functionn
		for the moment)'
	pic_name = 'the name of the tif image without the number'
	
	first_im = number of the first image to analyze
	
	n_stack = number of stacks(number of scans)
	
	xpix_in = initial pixel for loop on x coordinate
	xpix_fin = final pixel for loop on x coordinate
	
	ypix_in = initial pixel for loop on y coordinate
	ypix_fin = final pixel for loop on y coordinate
	
	fin = lenght of a delay scan(or how many images for each scan)
	'''
	

	#coordinates of the pixel to analyze

	dx = xpix_fin - xpix_in + 1
	dy = ypix_fin - ypix_in + 1
	
	
	#declare two zeros arraay for later
	delay= np.zeros(1001)
	intensity= np.zeros(shape=(1001, dx*dy+1))
	
	for i in range(0, fin):
		num = str((n_stack*fin)+(first_im+i))
		#print 'n_stack', n_stack
		#print 'num', num
		delay[i] = i
		im = Image.open(dir + pic_name+num+'.tif')
		pix = im.load()
		pos=0
		for x in range(xpix_in, xpix_fin+1):
			for y in range(ypix_in, ypix_fin+1):
				#print i, pos
				intensity[i,pos] = pix[x,y]
				pos = pos +1
	
	imarray = np.array(im)
	
	#plotting the delay scan at the pixel position xpix,ypix
	#plt.figure(2)
	#plt.plot(delay[0:fin-1], intensity[0:fin-1])
	
	#printng the .tif file with the pixel position
	#this part will be used to see where the rejected and passed scans come from. 
	#I am using imarray because I still have no idea how to plot pix, because I have no idea what it is
	
	#plt.figure(1)
	#plt.matshow(imarray)
	#plt.plot(xpix,ypix, 'ro')
	
	
	
	#plt.show()
	#im.show()
	
	return intensity, imarray
def select_good_scans(n_stack,intensity, xpix_in, xpix_fin, ypix_in, ypix_fin, fin, rejection):
	
	dx = xpix_fin - xpix_in + 1
	dy = ypix_fin - ypix_in + 1
	

	
	x_pas = np.zeros(dx*dy*(n_stack+1))
	y_pas = np.zeros(dx*dy*(n_stack+1))

	x_rej = np.zeros(dx*dy*(n_stack+1))
	y_rej = np.zeros(dx*dy*(n_stack+1))

	i_pas = 0
	i_rej = 0
	rej=0
	for i in range(0,dx*dy*(n_stack)):
		l_av = np.average(intensity[[0,5], i])
		c_av = np.average(intensity[[fin/2-100,fin/2+100], i])
		r_av= np.average(intensity[[fin-6,fin-1], i])
		if l_av - c_av>rejection and r_av - c_av>rejection and \
			np.amin(intensity[:, i])>100 and np.amax(intensity[:, i])<500:
				try:
					intensity_sum
				except NameError:
					#print "running for the first time"
					intensity_sum = intensity[:, i]
					x_pas[0] = xpix_in + int(i) / dy 
					y_pas [0] = ypix_in + int(i) % dy
					pas = 1
					
				else:
					#print "running for the", i+1, " time"
					#print 
					intensity_sum = (intensity[:,i] + intensity_sum)/2
					x_pas[pas] = xpix_in + int(i) / dy 
					y_pas [pas] = ypix_in + int(i) % dy
					pas = pas + 1

		else:
			x_rej[rej] = xpix_in + i / dy  
			y_rej [rej] = ypix_in + i % dy
			rej = rej+1
			

	x_pas_short = x_pas[0:pas]
	y_pas_short = y_pas[0:pas]
	x_rej_short = x_rej[0:rej]
	y_rej_short = y_rej[0:rej]
	#print 'xrej', x_rej_short
	#print 'y rej', y_rej_short
	print 'rejected', rej
	print 'passed', pas
	return intensity_sum, x_pas_short, y_pas_short, x_rej_short, y_rej_short
def smooth(inten, Nsm):

	#doing the math

	xint = np.arange(0, len(inten), 1)
	xder = np.empty(len(inten))
	der = np.empty(len(inten))
	
	# smooth		
	xsmooth = np.zeros(len(inten)/Nsm+1)
	smooth = np.zeros(len(inten)/Nsm+1)
	
	for x in range(0,len(inten)):
		xsmooth[int(x/Nsm)] = int(x)
		smooth[int(x/Nsm)] += inten[x]
	
	sder = np.zeros(len(inten)/Nsm+1)
	
	
	for x in range(1,len(inten)-1):
	#for x in inten:	
		der[x] = inten[x]-inten[x-1]
	
	#print 'number', (len(inten)-1)/Nsm-1, len(smooth), len(inten)
	for x in range(1,(len(inten)-1)/Nsm-1):
	#for x in smooth:	
		sder[x] = smooth[x]-smooth[x-1]
		
		
	return xsmooth[0:len(xsmooth)-1], smooth[0:len(xsmooth)-1], sder[0:len(xsmooth)-1]
def norm(xsmooth, smooth, smooth_der,Nsm):

	#Original dataset shows an increasing amplitude during the scan that is not related
	#width the effect we want to observe. we then normalize it:
	#averaging five points to the left and 5 to the right and drawing a line
	left_av = np.average(smooth[0:Nsm/3])
	right_av = np.average(smooth[-Nsm/3:-1])
	norm_line = left_av + (right_av-left_av)/(len(xsmooth)*Nsm)*xsmooth
	
	#correcting for the pendenza della retta
	smooth = smooth/norm_line
	
	#shifting to zero 
	smooth = smooth-np.amin(smooth)
	#print 'ss max', np.amin(ss)
	
	#normalizing to 1
	smooth = smooth/np.amax(smooth)
	smooth_der = smooth_der/np.amax(smooth_der)
	
	return xsmooth, smooth, smooth_der
def gaus(x,a,x0,sigma):
	return a*exp(-(x-x0)**2/(2*sigma**2))
	
def gaus3(x, a, a2, a3, x0, c, sigma):
	return (gaus(x, a1, x0-c, sigma)+gaus(x, a2, x0, sigma)+gaus(x, a3, x0+c, sigma))
	
def gaus5(x, a1, a2, a3, a4, a5, x0, c, sigma):
	return (gaus(x, a1, x0-2*c, sigma)+gaus(x, a2, x0-c, sigma)+gaus(x, a3, x0, sigma)+gaus(x, a4, x0+c, sigma)+gaus(x, a5, x0+2*c, sigma))

def gaus7(x, a1, a2, a3, a4, a5, a6, a7, x0, c, sigma):
	return (gaus(x, a1, x0-3*c, sigma)+gaus(x, a2, x0-2*c, sigma)+gaus(x, a3, x0-c, sigma)+gaus(x, a4, x0, sigma)+gaus(x, a5, x0+c, sigma)+gaus(x, a6, x0+2*c, sigma)+gaus(x, a7, x0+3*c, sigma))
	
def gaus9(x, a1, a2, a3, a4, a5, a6, a7, a8, a9, x0,c, sigma):
	return (gaus(x, a1, x0-4*c, sigma)+gaus(x, a2, x0-3*c, sigma)+gaus(x, a3, x0-2*c, sigma)+gaus(x, a4, x0-c, sigma)
	+gaus(x, a5, x0, sigma)+gaus(x, a6, x0+c, sigma)+gaus(x, a7, x0+2*c, sigma)+gaus(x, a8, x0+3*c, sigma)+gaus(x, a9, x0+4*c, sigma))

def gaus9_ds(x, a1, a2, a3, a4, a5, a6, a7, a8, a9, x0,c1, c2, sigma):
	return (gaus(x, a1, x0-4*c1, sigma)+gaus(x, a2, x0-3*c1, sigma)+gaus(x, a3, x0-2*c1, sigma)+gaus(x, a4, x0-c1, sigma)
	+gaus(x, a5, x0, sigma)+gaus(x, a6, x0+c2, sigma)+gaus(x, a7, x0+2*c2, sigma)+gaus(x, a8, x0+3*c2, sigma)+gaus(x, a9, x0+4*c2, sigma))

def gaus9_all(x, a1, a2, a3, a4, a5, a6, a7, a8, a9, x0,c1,c2, c3, c4, c6, c7, c8, c9, sigma):
	return (gaus(x, a1, x0-c1, sigma)+gaus(x, a2, x0-c2, sigma)+gaus(x, a3, x0-c3, sigma)+gaus(x, a4, x0-c4, sigma)
	+gaus(x, a5, x0, sigma)+gaus(x, a6, x0+c6, sigma)+gaus(x, a7, x0+c7, sigma)+gaus(x, a8, x0+c8, sigma)+gaus(x, a9, x0+c9, sigma))	
def gaus9_all_2sigma(x, a1, a2, a3, a4, a5, a6, a7, a8, a9, x0,c1,c2, c3, c4, c6, c7, c8, c9, sigma0, sigma):
	return (gaus(x, a1, x0-c1, sigma)+gaus(x, a2, x0-c2, sigma)+gaus(x, a3, x0-c3, sigma)+gaus(x, a4, x0-c4, sigma)
	+gaus(x, a5, x0, sigma0)+gaus(x, a6, x0+c6, sigma)+gaus(x, a7, x0+c7, sigma)+gaus(x, a8, x0+c8, sigma)+gaus(x, a9, x0+c9, sigma))

	
def find_select_maxima(intensity , perc, steps):
	#finding all the maxima
	max_x = np.array(argrelextrema(intensity, np.greater, order = steps))
	l = list(max_x.shape)
	max_y = np.zeros(l[1])
	
	for i in range(0,l[1]-1):
	    max_y[i] = intensity[max_x[0,i]]

	
	#selecting the interestesting ones: all the maxima lower than 5% of the
	#highest maxima will be discarded.
	
	disc = np.amax(max_y) * perc / 100
	
	sel_max_x = []
	sel_max_y = []

	
	for i in range(0,len(max_y)):
		if max_y[i] > disc:
			sel_max_x.append(max_x[0,i])
			sel_max_y.append(max_y[i])
	
	return sel_max_x, sel_max_y
	
def find_intervals(sel_max_x , intensity):
	'''this function defines automatically the intervals around the pics 
	where the fitting should be performed. It takes the data(intensity), 
	and an array where filled with the position of the maxima.
	I plan to make it better: it should find the minimum in the selected 
	intervals '''
	intervals_l = []
	intervals_r = []
	#trying to automatically select the fitting regions
	for i in range(0, len(sel_max_x)):
		#print 'i =', i
		if i == 0:
			#print 'i = ', i , 'done in i==0'
			intervals_l.append(0)
			intervals_r.append(sel_max_x[i]+np.argmin(intensity[sel_max_x[i]:(sel_max_x[i]+sel_max_x[i+1])/2]))
		elif i == len(sel_max_x)-1:
			intervals_l.append((sel_max_x[i-1]+sel_max_x[i])/2+np.argmin(intensity[(sel_max_x[i-1]+sel_max_x[i])/2:sel_max_x[i]]))
			intervals_r.append(len(intensity)-1)
		else :
			intervals_l.append(sel_max_x[i-1]+np.argmin(intensity[sel_max_x[i-1]:(sel_max_x[i-1]+sel_max_x[i])/2]))
			intervals_r.append(sel_max_x[i]+np.argmin(intensity[sel_max_x[i]:(sel_max_x[i]+sel_max_x[i+1])/2]))
			
	
	intervals_y = np.empty(len(intervals_l))
	intervals_y.fill(np.amax(intensity)/2)
	
	return intervals_l, intervals_r, intervals_y	
	
def fit_image(pixels, saw_on_pic,sel_max_x, sel_max_y, intervals_l, intervals_r, intensity):
	palette = ['r', 'g', 'b', 'c','m']
	peak = []
	peak_err = []
	fin = len(sel_max_x)
	for i in range(0,len(sel_max_x)):

		xf = pixels[intervals_l[i]:intervals_r[i]+1]
		yf = intensity[intervals_l[i]:intervals_r[i]+1] 
		n = len(xf)                          #the number of data
		mean = xf[np.argmax(yf)]                   #note this correction
		sigma = np.sqrt(sum(yf*(xf-mean)**2)/n )       #note this correction
		try:
			[amp,mean,sigma],pcov = curve_fit(gaus,xf,yf,p0=[1,mean,sigma])
			plt.plot(xf,gaus(xf,amp,mean,sigma),color = palette[i],label='peak '+str(i))
			print 'palette used', palette[i]
			peak.append(gaus(mean,amp,mean,sigma))
			# perr = np.sqrt(np.diag(pcov))
# 			peak_err.append(perr[0])
			plt.text(len(intensity)-50, np.amax(sel_max_y) - np.amax(sel_max_y) / 100 * (i+1) * 10, 'peak ' +str(i)+ '\n' +str(int(peak[i])), fontsize=15)
			plt.legend()
		
		except RuntimeError,IndexError: #this ignores if A fit does not work
			pass
			print 'I am skipping i =', i
			peak.append(0)
			# perr = 0
# 			peak_err.append(0)
			plt.text(len(intensity)-50, np.amax(sel_max_y) - np.amax(sel_max_y) / 100 * (i+1) * 10, 'peak ' +str(i)+ '\n not fit', fontsize=15)
		
		
	with PdfPages(saw_on_pic + '.pdf') as pdf:
		plt.figure(1)
		figure = plt.gcf()
		pdf.savefig(figure)
	
	return peak#, perr
		
def fit_single_peak(pixels, saw_on_pic,sel_max_x, sel_max_y, intervals_l, intervals_r, intensity):
	palette = ['r', 'g', 'b', 'c','m']
	peak = []
	peak_err = []

	xf = pixels[intervals_l:intervals_r]
	yf = intensity[intervals_l:intervals_r] 
	n = len(xf)                          #the number of data
	mean = xf[np.argmax(yf)]                   #note this correction
	sigma = np.sqrt(sum(yf*(xf-mean)**2)/n )       #note this correction
	try:
		[amp,mean,sigma],pcov = curve_fit(gaus,xf,yf,p0=[1,mean,sigma])
		plt.plot(xf,gaus(xf,amp,mean,sigma),color = palette[i],label='peak '+str(i))
		peak.append(gaus(mean,amp,mean,sigma))
		perr = np.sqrt(np.diag(pcov)) 
		peak_err.append(perr[0])
		plt.text(len(intensity)-50, sel_max_y[0] - np.amax(sel_max_y) * 20 / 100, 'peak 0 \n' +str(int(peak[0])), fontsize=15)
	
	
	except RuntimeError: #this ignores if A fit does not work
		pass
		print 'I am skipping i =', i
		plt.text(sel_max_x[0]-10, sel_max_y[0]+np.amax(sel_max_y) * 20 / 100, 'peak ' +str(0)+ '\n not fit', fontsize=15)
	
	return peak, perr

# Creating a routine that appends files to the output file
def append_pdf(input,output):
    [output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]


import sys
from numpy import NaN, Inf, arange, isscalar, asarray, array

def peakdet(v, delta, x = None):
    """
    Converted from MATLAB script at http://billauer.co.il/peakdet.html
    
    Returns two arrays
    
    function [maxtab, mintab]=peakdet(v, delta, x)
    %PEAKDET Detect peaks in a vector
    %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
    %        maxima and minima ("peaks") in the vector V.
    %        MAXTAB and MINTAB consists of two columns. Column 1
    %        contains indices in V, and column 2 the found values.
    %      
    %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
    %        in MAXTAB and MINTAB are replaced with the corresponding
    %        X-values.
    %
    %        A point is considered a maximum peak if it has the maximal
    %        value, and was preceded (to the left) by a value lower by
    %        DELTA.
    
    % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
    % This function is released to the public domain; Any use is allowed.
    
    """
    maxtab = []
    mintab = []
       
    if x is None:
        x = arange(len(v))
    
    v = asarray(v)
    
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    
    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    
    lookformax = True
    
    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)
    
    
def find_nearest_index(array,value):
	idx = (np.abs(array-value)).argmin()
	return idx


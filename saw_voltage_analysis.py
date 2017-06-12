#!/usr/bin/env python


import numpy as np
import numexpr as ne
import matplotlib.pyplot as plt
import pylab as plb
from scipy.optimize import curve_fit
from scipy.optimize import least_squares
import time
import matplotlib.colors as colors
import sys, os, re
sys.path.append('specscan')
import specscan as specscan
import string
from analysis_lib import *




class extract_data():
	''''''
	
	def __init__(self, sample, first_scan, last_scan, V_step, dir, x, y):
		self.sample = sample
		self.fs = first_scan
		self.ls = last_scan
		self.V_step = V_step
		self.dir = dir
		self.x = x
		self.y = y
		if not os.path.exists('intermediate'):
			os.mkdir('intermediate')
	def voltage_array(self):
		'''This functions returns an array of  voltages, and it saves it in the intermediate folder'''
		V_fin = (self.ls-self.fs)*self.V_step
		voltage = np.arange(0, V_fin+self.V_step, self.V_step)
		np.savetxt('intermediate/'+self.sample+'_voltage.dat', voltage, fmt='%.18e', delimiter=' ', newline='\n')
		return voltage
	
	def extract_spec(self):
		''' This method extract the selected scan from a spec file.
		It returns a matrix where the columns are the scan, and a vector for the angular position.
		Additionally it saves these two feature in the intermediate folder.'''
		spec=specscan.SpecFile(self.dir)
		for i in range(self.fs,self.ls):
			print 'i', i
			a=spec.get_scan_num(i)
			#print 'a', a
			if i == self.fs:
				theta = a.data[self.x]
			intensity = a.data[self.y]
			try:
				intensity_all = np.concatenate((intensity_all,intensity), axis=0)

			except NameError :
				intensity_all = intensity
		intensity_all = intensity_all.reshape((self.ls-self.fs,intensity.size))
		np.savetxt('intermediate/'+self.sample+'_extracted_int.dat', intensity_all, fmt='%.18e', delimiter=' ', newline='\n')
		np.savetxt('intermediate/'+self.sample+'_extracted_th.dat', theta, fmt='%.18e', delimiter=' ', newline='\n')
		return intensity_all.reshape((self.ls-self.fs,intensity.size)), theta

	def extract_csv(self):
		print 'Function currently non implemented.'
		print 'Hopefully beamlines do not save the data in csv'



class voltage_scan():
	''' This class was tested only with data from sample where the 0-th order is always the stronger in the diffraction
	pattern.	
	TO DO: automatically guess the distance between the peaks'''
	def __init__(self, sample):
		self.sample = sample
		if not os.path.exists('intermediate'):
			os.mkdir('intermediate')
			
		#loading the intensity and theta files
		self.theta = np.loadtxt('intermediate/'+self.sample+'_extracted_th.dat')
		self.intensity = np.loadtxt('intermediate/'+self.sample+'_extracted_int.dat')
		
	def normalize(self):
		first = self.intensity[0,:]
		max_int = np.amax(first)
		self.intensity = self.intensity/max_int
		np.savetxt('intermediate/'+self.sample+'_normalized_intensity.dat', self.intensity)
		return self.intensity
	
	def find_shift(self):
		first = self.intensity[0,:]
		max_th = np.argmax(first)
		shift = []
		for m in range(0,self.intensity.shape[0]):
			mth = first = self.intensity[m,:]
			maxm = np.argmax(mth)
			shift.append(self.theta[maxm] - self.theta[max_th])
		np.savetxt('intermediate/'+self.sample+'_shift.dat', shift)
		return shift
		
	def find_maxima(self, plot):
		self.plot = plot
		delta = 0.01
		start = self.theta[0]
		stop = self.theta[len(self.theta)-1]
		step = (stop-start)/len(self.theta)
		shift = np.loadtxt('intermediate/'+self.sample+'_shift.dat')
		for m in range(0,self.intensity.shape[0]):
			maxtab, mintab = peakdet(self.intensity[m,:],delta)
			#~ print 'run', m
			plt.figure(m)
			#sel_max_x = theta[int(maxtab[:,0])]
			sel_max_x = start + maxtab[:,0]*step
			#~ print 'x', sel_max_x
			sel_max_y = maxtab[:,1]
			#~ print 'y', sel_max_y
			#~ print sel_max_y

			#saving the maxima to files
			np.savetxt('intermediate/'+self.sample+'_int_max_'+str(m*10)+' V'+'.dat', sel_max_y)
			np.savetxt('intermediate/'+self.sample+'_th_max_'+str(m*10)+' V'+'.dat', sel_max_x)
			if self.plot == 1:
				plt.figure(m+100)
				plt.plot(sel_max_x-shift[m], sel_max_y, 'ko', label = 'maxima')
				plt.plot(self.theta-shift[m] , self.intensity[m,:], label = str(m*10)+' V')
				plt.title(str(m*10)+' V')
				plt.savefig('intermediate/'+self.sample+'_'+str(m*10)+' V'+'.pdf')
				plt.savefig('intermediate/'+self.sample+'_'+str(m*10)+' V'+'.png')
				plt.legend()
		#~ if self.plot == 1:
			#~ plt.show()
		#~ plt.clf()
		
	def fit_voltage_scan(self, delta_theta, show_plot):
		'''This methods works only if the data have been normalized, and if the shift has been calculated, 
		and the maxima have been found'''
		self.delta_theta = delta_theta
		self.show_plot = show_plot
		#~ fitting the V=0 scan, just to find initial parameters for the fit 
		intensity = self.intensity[0,:] #selecting the first scan, V=0
		mean = self.theta[np.argmax(intensity)]
		idx = (np.abs(intensity-0.5)).argmin()
		fwhm = 2*np.abs(mean - self.theta[idx])
		#~ print 'mean', mean
		guess_all = [0,0,0,0,1,0,0,0,0, mean, self.delta_theta*4, self.delta_theta*3, self.delta_theta*2, 
		self.delta_theta*1, self.delta_theta*1, self.delta_theta*2, self.delta_theta*3, self.delta_theta*4, fwhm/2.35,fwhm/2.35  ]
		shift = np.loadtxt('intermediate/'+self.sample+'_shift.dat')
		m0 = []
		m1 = []
		m2 = []
		m3 = []
		m4 = []
		for m in range(0,self.intensity.shape[0]):
			#~ creating an array for plotting 
			xplot = np.arange(self.theta[0], self.theta[len(self.theta)-1]+shift[m], 0.00001)
			x = self.theta - shift[m] #shifting the array to be centered
			xplot = xplot - shift[m]  #shifting the array for plotting of the same amount	
			intensity = self.intensity[m,:] #selecting the scan number m to be fit
			#~ loading the max in th and intensity
			max_int = np.loadtxt('intermediate/'+self.sample+'_int_max_'+str(10*10)+' V'+'.dat')
			max_th = np.loadtxt('intermediate/'+self.sample+'_th_max_'+str(10*10)+' V'+'.dat')
			#~ calculating the mean to guess it for the fit
			mean = max_th[np.argmax(max_int-1)] - shift[m]
			#~ FITTING
			[amp4l,amp3l, amp2l, amp1l,amp,amp1r,amp2r,amp3r,amp4r,mean,c1,c2, c3, c4, c6, c7, c8, c9,  sigma0, sigma],pcov 					= curve_fit(gaus9_all_2sigma, x, intensity, guess_all)
			#~ Updating the guess for the next iteration with the results of the fit
			guess = [amp4l,amp3l, amp2l, amp1l,amp,amp1r,amp2r,amp3r,amp4r,mean,c1,c2, c3, c4, c6, c7, c8, c9,  sigma0, 					sigma]
			#~ Plotting the results of the fit with the data
			plt.figure(m)
			plt.title(str(m*10)+' V')
			plt.plot(xplot, gaus9_all_2sigma(xplot, amp4l,amp3l, amp2l, amp1l,amp,amp1r,amp2r,amp3r,amp4r,mean,c1,c2, c3, c4										, c6, c7, c8, c9,  sigma0, sigma), 'r', label = 'gaussian fit')
			plt.plot(x , self.intensity[m,:], label = str(m*10)+' V')
			#~ Saving the values of the fit
			m0.append(amp) 
			m1.append((amp1l+amp1r)/2)
			m2.append((amp2l+amp2r)/2)
			m3.append((amp3l+amp3r)/2)
			m4.append((amp4l+amp4r)/2)
			np.savetxt('intermediate/'+self.sample+'_m'+str(m*10)+'_par.txt', (amp4l,amp3l, amp2l, amp1l,amp,amp1r,amp2r,												       amp3r,amp4r,  mean, c1,c2, c3, c4, c6, c7, c8, c9,  sigma0, sigma  ))  	
			guess = [amp4l,amp3l, amp2l, amp1l,amp,amp1r,amp2r,amp3r,amp4r,mean,c1,c2, c3, c4, c6, c7, c8, c9,  sigma0, 				     sigma]
		
		np.savetxt('intermediate/'+self.sample+'_m0.dat', m0)
		np.savetxt('intermediate/'+self.sample+'_m1.dat', m1)
		np.savetxt('intermediate/'+self.sample+'_m2.dat', m2)
		np.savetxt('intermediate/'+self.sample+'_m3.dat', m3)
		np.savetxt('intermediate/'+self.sample+'_m4.dat', m4)
		#~ if self.show_plot == 1:
			#~ plt.show()
		#~ plt.clf()
	
	def intensity_vs_voltage(self, V_in, V_fin,V_step,show_plot):
		self.V_in = V_in
		self.V_fin = V_fin
		self.V_step = V_step
		self.show_plot = show_plot
		voltage = np.arange(self.V_in,self.V_fin+1,self.V_step)
		
		m0 = np.loadtxt('intermediate/'+self.sample+'_m0.dat')
		m1 = np.loadtxt('intermediate/'+self.sample+'_m1.dat')
		m2 = np.loadtxt('intermediate/'+self.sample+'_m2.dat')
		m3 = np.loadtxt('intermediate/'+self.sample+'_m3.dat')
		m4 = np.loadtxt('intermediate/'+self.sample+'_m4.dat')
		#plotting
		fig = plt.figure(1000)
		ax = fig.add_subplot(111)
		ax.plot(voltage,m0, 'ro', label = 'm=0')
		ax.plot(voltage,m1, 'bo', label = 'm=1')
		ax.plot(voltage,m2, 'go', label = 'm=2')
		ax.plot(voltage,m3, 'mo', label = 'm=3')
		ax.plot(voltage,m4, 'co', label = 'm=4')
		plt.setp(ax.get_xticklabels(), visible=False)
		plt.legend()
		plt.title('Intensity/Voltage')
		plt.xlabel('Voltage [V]')
		plt.ylabel('intensity [a.u.]')
		plt.savefig('intermediate/'+self.sample+'_voltage_orders.png')
		#~ if self.show_plot == 1:
			#~ plt.show()
		#~ plt.clf()
		



def test_extract_data():
	print 'Testing the class extract_from_spec'
	dir = 'data/2017-05-18_sample_M1_01.spec'
	extracted = extract_data('test',1,12,10,dir,'eta', 'cyber')
	intensity_all, th = extracted.extract_spec()
	print 'test complete'
	
def test_voltage_scan():
	print 'Testing the class voltage_scan'
	vs = voltage_scan('test')
	i = vs.normalize()
	shift = vs.find_shift()
	vs.find_maxima(plot = 1)
	vs.fit_voltage_scan(delta_theta = 0.004, show_plot = 0)
	vs.intensity_vs_voltage(0,100,10, show_plot = 0)
	plt.show()
	print 'test complete'
	
	
if __name__ == "__main__":
	#~ test_extract_data()
	test_voltage_scan()
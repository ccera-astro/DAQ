import numpy
import matplotlib.pyplot as plot
import os
import ClassReadDynSpecFile as crdsf
import time

class plot21() :

    def __init__(self):
        
        self.f = crdsf.GnuRadioMetaFile()	                # Create an instance of the dynamic file reader

        # temporary fix to deal with bad channel 1 
        self.fName = 'raw2.dat'    
        self.fileInfo = self.f.gopen(self.fName)	        # Open the file to be read
        print("File information={0:s}".format(self.fileInfo))	# Display the file info
        self.FFTsize = self.fileInfo['n_freq']
        fSample = 1.e-6*self.fileInfo['rx_rate']*self.fileInfo['N_average']
        self.fCenter = 1.e-6*self.fileInfo['freq']
        print "fCenter={0:f} MHz  fSample={1:f}".format(self.fCenter,fSample)
        fMin = self.fCenter - 0.5*fSample
        fMax = self.fCenter + 0.5*fSample
        self.freqs = numpy.linspace(fMin,fMax,self.FFTsize)
        
        # get Doppler velocites 
        fLine = 1420.406   # in MHz
        c = 3.0e5          # in km/s
        self.velocities = c*(self.freqs/fLine - 1.)

        # get gain correction
        self.gain = numpy.fromfile('gain.dat',dtype=float)
        if self.fName == 'raw2.dat' : self.gain *= 3.0
        
        # number of spectra
        self.count = 0

    def getData(self) :

        power = numpy.zeros(self.FFTsize)
        nRead, nEmpty = 0, 0
        while nRead*nEmpty == 0 :
            data = self.f.gnext()		# get the new data
	    if data[0] == 0 :		# if no new data
		time.sleep(0.5)
                nEmpty += 1
	    else:
		ts = data[1]	# get the timestamps
                tAvg = numpy.mean(ts) 
                nRecords = len(ts)
		spec = data[2]	# get the spectral data
                power += data[2][0]
                nRead += 1
                
        power /= nRead
        return nRead, tAvg, power

    def initPlot(self,args):

        # Plot total power vs. time
        self.fig = plot.figure(figsize=(12, 10), dpi=80)
        self.ax = self.fig.add_subplot(111)
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        self.fig.canvas.set_window_title('live21.py') 
        #self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim([-200.,200.])
        nRecords, tAvg, power = self.getData()
        self.sumPower = numpy.zeros_like(power) 
        self.li, = self.ax.plot(self.velocities, power, 'b.')
        if not args.sunMode : self.ax.set_ylim([-5.,50.])
        self.ax.set_title("PSD vs Approach Velocity")
        self.ax.set_xlabel("v (km/s)")
        self.ax.set_ylabel("PSD (K)")
        self.ax.grid()
        self.fig.canvas.draw()
        plot.show(block=False)

    def plotNewSpectrum(self,args,alpha) :
    
        nRecords, tAvg, power = self.getData()
        power = numpy.divide(power,self.gain)     # gain correction
        if not args.sunMode :
            power -= self.getBackground(power)

        if False :
            self.count += 1
            if alpha > 0. : oneOverAlpha = int(1./alpha) 
            if alpha > 0  and self.count >= oneOverAlpha :
                if self.count == oneOverAlpha: self.sumPower = self.sumPower/self.count 
                self.sumPower = alpha*power + (1. - alpha)*self.sumPower 
                power = self.sumPower
            else :
                self.sumPower += power 
                power = self.sumPower/self.count
        else :
            self.sumPower = alpha*power + (1. - alpha)*self.sumPower 
            power = self.sumPower

        if args.sunMode :
            yMax = 1.1*numpy.max(power)
            self.ax.set_ylim([0.,yMax])
            
        mask = [510,511,512,513,514,664,665,666,667,668]
        maskedPower = numpy.delete(power,mask)
        maskedVelocities = numpy.delete(self.velocities,mask)
        #self.ax.set_ylim([-2.0,max(10.,1.1*max(power))])
        if args.noNotch :
            self.li.set_xdata(self.velocities)
            self.li.set_ydata(power)
        else :
            self.li.set_xdata(maskedVelocities)
            self.li.set_ydata(maskedPower)
        self.fig.canvas.draw()
        plot.pause(0.1)
        return
    
    # Fit the spectrum to a 2nd order polynomial
    # Omit the signal region and the ends of the spectrum
    # from the fit.

    def getBackground(self,power) :
        f1Min, f1Max, f2Min, f2Max = 1418.5, 1419.5, 1421., 1422. 
        xPoints, yPoints = [], []
        for i in range(len(self.freqs)) :
            f = self.freqs[i]
            if (f > f1Min and f < f1Max) or (f > f2Min and f < f2Max) :
                xPoints.append(f - self.fCenter)
                yPoints.append(power[i]) 

        pars = numpy.polyfit(xPoints, yPoints, 1)
        #print ("In plot21.getBackground pars={0:s}".format(str(pars)))
        background = pars[1] + pars[0]*(self.freqs-self.fCenter)
        if self.fName == 'raw2.dat' : background -= 2.0
        return background

    def zeroPower(self) :
        self.sumPower = numpy.zeros(len(self.sumPower))
        

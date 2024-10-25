import numpy as np
import matplotlib.pyplot as plot
import time

class plotDoppler() :

    def __init__(self, file_name, metadata):
        
        
        self.FFTsize = metadata['fft_size']
        self.metadata = metadata

        #fSample = 1.e-6*self.fileInfo['rx_rate']*self.fileInfo['N_average']
        self.fCenter = 1.0e-6*metadata['freq']
        fSample = 1.0e-6*metadata["srate"]
        print("In plot21.__init__: fCenter={0:f} MHz  fSample={1:f}".format(self.fCenter,fSample))
        fMin = self.fCenter - 0.5*fSample
        fMax = self.fCenter + 0.5*fSample
        self.freqs = np.linspace(fMin,fMax,self.FFTsize)
        
        # get Doppler velocites 
        fLine = 1420.406   # in MHz
        c = 3.0e5          # in km/s
        self.velocities = c*(self.freqs/fLine - 1.)

        self.gain = 1.   # get gain correction 
        self.file_name = file_name 
        self.count = 0   # number of spectra
        self.offset = 0   # file read offset

    def getData(self) :
        nRead = 0 
        power = np.zeros(self.FFTsize)
        f = open(self.file_name,"rb")
        while True :
            data = np.fromfile(f,count=self.FFTsize,offset=self.offset,dtype=np.float32)
            print("In getData() len(data)={0:d} nRead={1:d}".format(len(data),nRead))
            if len(data) >= self.FFTsize : 
                power += data 
                nRead += 1 
                self.offset += 4*self.FFTsize 
            else :
                if nRead > 0 : power /= nRead
                break         
        print("Exiting getData(): nRead={0:d}".format(nRead))
        return nRead, power
    
    def fitBackground(self,vDoppler,power,n,vSignal) :
        weights = np.ones_like(vDoppler)
        for i in range(len(vDoppler)) :
            if abs(vDoppler[i]) < vSignal : weights[i] = 1.e-6 
        series = np.polynomial.chebyshev.Chebyshev.fit(vDoppler, power, n, w=weights)
        background = series(vDoppler) 
        return background
    
    def anaSpectrum(self,power) :
        power *= 1.10e5
        vMin, vMax = -300., 300.
        i1 = np.searchsorted(self.velocities,vMin)
        i2 = np.searchsorted(self.velocities,vMax)
        fs = self.freqs[i1:i2]
        vDoppler = self.velocities[i1:i2]
        power = power[i1:i2]
        background = self.fitBackground(vDoppler,power,5,200.)
        return vDoppler, power-background 

    def initPlot(self,args):
        print("Enter initPlot()")
        self.fig = plot.figure(figsize=(12, 10), dpi=80)
        self.ax = self.fig.add_subplot(111)
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        self.fig.suptitle('Live Doppler Display') 
        self.ax.set_xlim([-200.,200.])
        nRecords, power = self.getData()
        self.sumPower = np.zeros_like(power) 
        vDoppler, bkgr_sub_pow = self.anaSpectrum(power)
        self.li, = self.ax.plot(vDoppler, bkgr_sub_pow, 'b.')
        if not args.sun_mode : self.ax.set_ylim([-5.,50.])
        self.ax.set_title("PSD vs Approach Velocity")
        self.ax.set_xlabel("v (km/s)")
        self.ax.set_ylabel("PSD (K)")
        self.ax.grid()
        self.fig.canvas.draw()
        plot.show(block=False)
        print("Leaving init_plot()")

    def plotNewSpectrum(self,args,alpha) :    
        nRecords, power = self.getData()
        print("In plotNewSpectrum() nRecords={0:d}".format(nRecords))
        if nRecords > 0 :
            self.sumPower = alpha*power + (1. - alpha)*self.sumPower 
            power = self.sumPower
            vDoppler, bkgr_sub_pow = self.anaSpectrum(power)
            self.li.set_xdata(vDoppler)
            self.li.set_ydata(bkgr_sub_pow)

        if args.sun_mode :
            yMax = 1.1*np.max(power)
            self.ax.set_ylim([0.,yMax])
            
        self.fig.canvas.draw()
        plot.pause(0.1)
        return
    
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

        self.gain = 0.33   # get gain correction 
        self.file_name = file_name 
        self.base_name = file_name.split("/")[-1].split("_")[0]  
        self.count = 0   # number of spectra
        self.offset = 0   # file read offset
        self.draw_count = 0 
        self.read_count = 0 

    def getData(self) :
        nRead = 0 
        power = np.zeros(self.FFTsize)
        f = open(self.file_name,"rb")
        f.seek(self.offset)
        data = self.gain*np.fromfile(f,count=self.FFTsize,dtype=np.float32)
        #print("In getData() len(data)={0:d} nRead={1:d}".format(len(data),nRead))
        if len(data) >= self.FFTsize : 
            power += data 
            nRead += 1 
            self.offset += 4*self.FFTsize 
        self.read_count += 1       
        #print("Exiting getData(): nRead={0:d} offset={1:d} read_count={2:d}".format(
        #   nRead,self.offset,self.read_count))
        return nRead, power
    
    def fitBackground(self,vDoppler,power,n,vSignal) :
        weights = np.ones_like(vDoppler)
        for i in range(len(vDoppler)) :
            if abs(vDoppler[i]) < vSignal : weights[i] = 1.e-6 
        series = np.polynomial.chebyshev.Chebyshev.fit(vDoppler, power, n, w=weights)
        background = series(vDoppler) 
        return background
    
    def anaSpectrum(self,power) :
        p = 0.25*1.10e5*power
        vMin, vMax = -300., 300.
        i1 = np.searchsorted(self.velocities,vMin)
        i2 = np.searchsorted(self.velocities,vMax)
        fs = self.freqs[i1:i2]
        vDoppler = self.velocities[i1:i2]
        p = p[i1:i2]
        background = self.fitBackground(vDoppler,p,5,200.)
        return vDoppler, p-background 

    def initPlot(self,args):
        print("Enter initPlot()")
        self.fig = plot.figure(figsize=(12, 8), dpi=80)
        self.ax = self.fig.add_subplot(111)
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        self.fig.suptitle('Live Doppler Display',fontsize=14) 
        self.ax.set_xlim([-200.,200.])
        nRecords, power = self.getData()
        #self.sumPower = np.zeros_like(power) 
        self.sumPower = power 
        vDoppler, bkgr_sub_pow = self.anaSpectrum(power)
        self.li, = self.ax.plot(vDoppler, bkgr_sub_pow, 'b.')
        self.draw_count += 1 
        self.ax.set_title("PSD vs Approach Velocity: Draw count={0:d}".format(self.draw_count))
        self.ax.set_xlabel("v (km/s)")
        self.ax.set_ylabel("PSD (K)")
        self.ax.grid()
        self.fig.canvas.draw()
        plot.show(block=False)
        print("Leaving init_plot()")
        

    def plotNewSpectrum(self,args,alpha) :  
        alph = max(1./(self.draw_count + 1.),alpha)   
        nRead, power = self.getData()
        print("In plotNewSpectrum() nRead={0:d} alpha={1:f} alph={2:f} draw_count={3:d}".format(nRead,alpha,alph,self.draw_count))
        if nRead > 0 :
            self.sumPower = alph*power + (1. - alph)*self.sumPower 
            vDoppler, bkgr_sub_pow = self.anaSpectrum(self.sumPower)
            self.li.set_xdata(vDoppler)
            self.li.set_ydata(bkgr_sub_pow)
            yMax, yMin = np.max(bkgr_sub_pow), np.min(bkgr_sub_pow)
            dy = yMax - yMin 
            self.ax.set_ylim([yMin - 0.1*dy,yMax + 0.1*dy])

        if args.sun_mode :
            yMax = 1.1*np.max(power)
            self.ax.set_ylim([0.,yMax])
            
        self.ax.set_title("PSD vs Approach Velocity: {0:s} Draw count={1:d} alpha={2:.4f}".format(self.base_name,self.draw_count,alph))
        self.fig.canvas.draw()
        self.draw_count += 1 
        plot.pause(0.1)
        return
    
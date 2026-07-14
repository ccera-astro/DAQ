import numpy as np
import matplotlib.pyplot as plot
import time

class plotScan() :

    def __init__(self, file_name, metadata):
        
        self.FFTsize = metadata['fft_size']
        self.metadata = metadata
        self.fCenter = 1.0e-6*metadata['freq']
        fSample = metadata["srate"]
        D = metadata['decimation_factor']
        self.tStep = 1./(fSample/D/self.FFTsize)
        print("In plotScan.__init__: fCenter={0:f} MHz  fSample={1:f} tStep={2:.2f} ms".format(self.fCenter,fSample,1000.*self.tStep))

        self.gain = 1.   # get gain correction 
        self.file_name = file_name 
        self.max_read = 4 
        self.count = 0   # number of spectra
        self.offset = 0   # file read offset
        self.draw_count = 0 
        self.read_count = 0 

    def getData(self) :
        nRead = 0 
        power = [] 
        f = open(self.file_name,"rb")
        while nRead < self.max_read :
            data = np.fromfile(f,count=self.FFTsize,offset=self.offset,dtype=np.float32)
            print("    In getData() len(data)={0:d} nRead={1:d}".format(len(data),nRead))
            if len(data) >= self.FFTsize : 
                power.append(np.sum(data)) 
                nRead += 1 
                self.offset += 4*self.FFTsize 
            else :
                break  
        self.read_count += 1       
        print("    Exiting getData(): nRead={0:d} offset={1:d} read_count={2:d} len(power)={3:d}".format(
            nRead,self.offset,self.read_count,len(power)))
        return nRead, power
    
    def getTimeLimits(self, t) :
        tScales = [10., 20., 50., 100., 200., 500., 1000., 2000., 5000., 10000., 20000., 50000., 100000.]
        tMax = t[-1]
        for tScale in tScales :
            if tMax < tScale :return [0., tScale]
        return [0., tMax]
    
    def initPlot(self,args):
        print("Enter plotScan.initPlot()")
        self.fig = plot.figure(figsize=(12, 8), dpi=80)
        self.ax = self.fig.add_subplot(111)
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        self.fig.suptitle('Live Scan Display',fontsize=14) 
        nRecords, short_series = self.getData()
        self.tMax = nRecords*self.tStep
        self.times = np.linspace(0.,self.tMax,nRecords)
        self.powers = short_series  
        self.li, = self.ax.plot(self.times,self.powers, 'b.')
        self.ax.set_xlim(self.getTimeLimits(self.times)) 
        self.draw_count += 1 
        self.txt1 = self.ax.text(-180.,40.,"Draw count={0:d}".format(self.draw_count),fontsize=14)
        self.ax.set_title("Power vs Time")
        self.ax.set_xlabel("t (s)")
        self.ax.set_ylabel("PSD (K)")
        self.ax.grid()
        self.fig.canvas.draw()
        plot.show(block=False)
        print("   In init_plot() times[-5:]={0:s}".format(str(self.times[-5:])))
        print("   Leaving init_plot()")
        
    def plotNewSeries(self,args) :  
        print("Entering plotNewSeries()")
        nRecords, short_series = self.getData()
        print("In plotNewSeries() nRecords={0:d} draw_count={1:d}".format(nRecords,self.draw_count))
        if nRecords > 0 :
            tMin = self.tMax + self.tStep 
            self.tMax += nRecords*self.tStep 
            self.times = np.concatenate((self.times,np.linspace(tMin,self.tMax,nRecords)))
            self.powers = np.concatenate((self.powers,short_series))
            self.li.set_xdata(self.times)
            self.li.set_ydata(self.powers)
            yMax = 1.1*np.max(self.powers)
            self.ax.set_xlim(self.getTimeLimits(self.times)) 
            self.ax.set_ylim([0.,yMax])
            print("   In plotNewSeries() len(times)={0:d} yMax={1:f} powers[-1]={2:f}".format(len(self.times),yMax,self.powers[-1]))
            print("   In plotNewSeries() times[-5:]={0:s}".format(str(self.times[-5:])))

        self.txt1.set_text("Draw count={0:d}".format(self.draw_count))
        self.fig.canvas.draw()
        self.draw_count += 1 
        plot.pause(0.1)
        return
    
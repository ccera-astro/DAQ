import numpy as np
import runPolyco as rp 
import matplotlib.pyplot as plot
import time
import scipy.stats as stats 

class plotPulsar() :

    def __init__(self, base_name, metadata):
        
        # We play a trick here.   The added factor of 4 means that we are 
        # effectively averaging four data points    
        
        self.FFTsize = metadata['fft_size']
        self.count = 32*50000

        self.metadata = metadata
        self.fCenter = 1.0e-6*metadata['freq']
        fSample = metadata["srate"]
        D = metadata['decimation_factor']
        self.tStep = 1./(fSample/D/self.FFTsize)
        self.time_offset = 0. 

        self.gain = 1.   # get gain correction 
        self.file_name_1 = base_name + "_1.raw" 
        self.file_name_2 = base_name + "_2.raw" 
        self.offset = 0   # file read offset
        self.draw_count = 0 
        self.read_count = 0 
        print("In plotPulsar.__init__: fCenter={0:f} MHz  fSample={1:f} tStep={2:.6f} self.count={3:d}".format(
            self.fCenter,fSample,self.tStep,self.count))
        self.nPhaseBins = 50 
        self.bdata_accum, self.bnum_accum = np.zeros(self.nPhaseBins), np.zeros(self.nPhaseBins)

    def getData(self) :
        nRead = 0 
        times, power = np.array([]), np.array([])
        FFTsize = self.FFTsize 
        f1 = open(self.file_name_1,"rb")
        f1.seek(self.offset)
        data = np.fromfile(f1,count=self.count,dtype=np.float32)
        items_read = len(data)
        print("    In getData() offset={0:d} items_read={1:d} len(data)={2:d} nRead={3:d}".format(self.offset,items_read,len(data),nRead))
        print("    In getData() tStep={0:.6f} time_offset={1:.6f}".format(self.tStep,self.time_offset)) 
        if items_read < self.count :
            print("    Exiting getData3() too little data")  
            return 0, times, power 
        else :
            cols = FFTsize
            rows = int(len(data)/FFTsize)
            data = np.reshape(data, (rows,cols)) 
            power = np.sum(data,1)
            f2 = open(self.file_name_2,"rb")
            f2.seek(self.offset)
            data = np.fromfile(f2,count=self.count,dtype=np.float32)
            if len(data) < self.count :
                print("**** ERROR file2 data smaller than file1 data.  Read {0:d} from file1 and {1:d} from file2".format(items_read,len(data)))
                return 0, np.array([]), np.array([]) 
            data = np.reshape(data, (rows,cols)) 
            power += np.sum(data,1)

            times = np.linspace(0.,len(power)*self.tStep,len(power))
            times += self.time_offset
            self.offset += 4*items_read
            self.time_offset += self.tStep*len(times) 
            nRead = len(power)
            print("    Exiting getData3() nRead={0:d} offset={1:d} read_count={2:d} len(power)={3:d}".format(
            nRead,self.offset,self.read_count,len(power)))
            #print("    Exiting getData3() times[:4]={0:s} times[-4:]={1:s}".format(str(times[:4]),str(times[-4:])))
            return nRead, times, power

    def initAna(self,base_name,metadata) :
        self.MJD0 = ((metadata['t_start'])/ 86400.) + 40587.
        self.coeff = rp.getpolycoeff(self.MJD0, metadata, base_name)
        return 

    def time2phase(self, time, best_coeff):	#Converts a set of times (mjd) into phases for the specified pulsar
        # these define the indices	
        TMID = 1
        RPHASE = 3
        F0 = 4
        coeff1 = 6
        coeff2 = 7
        coeff3 = 8
        coeff4 = 9

        dt = (time - best_coeff[TMID]) * 1440.0

        # Construct the polynomial coefficients	
        pcoeff = (best_coeff[RPHASE] + best_coeff[coeff1], 60.0 * best_coeff[F0] + best_coeff[coeff2], best_coeff[coeff3], best_coeff[coeff4]) 
        phase = np.polynomial.polynomial.polyval(dt, pcoeff)
        return phase

    def bindata( self, phase, value, NumBins):	# Averages 'value' into 'NumBins' bins based on the 'phase' values
        mphase = phase - np.floor(phase)
        iphase = np.floor(mphase * NumBins)
        bdata = np.zeros((NumBins))
        bnum = np.zeros((NumBins))

        (bdata,d1,d2) = stats.binned_statistic(iphase, value, statistic='sum', bins=NumBins, range = [0,NumBins-1])
        (bnum,d1,d2) = stats.binned_statistic(iphase, value, statistic='count', bins=NumBins, range = [0,NumBins-1])

        return (bdata, bnum)

    def anaPulsar(self, times, power) :
        # histogram power series and update cumulative histogram
        MJDs = self.MJD0 + times/86400. 
        phase = self.time2phase(MJDs, self.coeff)
        print("In anaPulsar(): len(phase)={0:d} len(power)={1:d}".format(len(phase),len(power)))
        #print("In anaPulsar(): \nphase[0:5]={0:s} \npower[0:5]={1:s}".format(str(phase[:5]),str(power[:5]))) 
        bdata, bnum = self.bindata(phase, power, self.nPhaseBins)
        self.bdata_accum += bdata
        self.bnum_accum += bnum 
        phase_hist = np.divide(self.bdata_accum,self.bnum_accum)
        #print("In anaPulsar() phase_hist mean={0:.6f} rms={1:.6f}".format(np.mean(phase_hist),np.std(phase_hist)))
        return phase_hist 

    def getSigmaArray(self,x) :
        iMax = np.argmax(x)
        # remove phase bins within +/- 3 of peak 
        iLow, iHigh = max(0,iMax-3), min(len(x),iMax+3)
        y = np.delete(x,range(iLow,iHigh))
        mean, sigma = np.mean(y), np.std(y)
        xx = (x-mean)/sigma 
        return xx
     
    def initPlot(self,args):
        print("Enter plotPulsar.initPlot()")
        self.fig = plot.figure(figsize=(12, 8), dpi=80)
        self.ax = self.fig.add_subplot(111)
        
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        self.fig.suptitle('Live Pulsar Display',fontsize=14) 
    #   read data
        nRecords, short_times, short_series = self.getData()
        print("In initPlot(): nRecords={0:d}".format(nRecords))
        phase_hist = self.anaPulsar(short_times,short_series)
        phase_bins = np.linspace(0.,1.,self.nPhaseBins)
        sigma_array = self.getSigmaArray(phase_hist)
        best_sigma = max(sigma_array)
        yMin, yMax = -4., max(4.,np.max(sigma_array)) 
        dy = yMax - yMin
        self.ax.set_ylim(yMin-0.1*dy,yMax+0.1*dy) 
        x_err = np.zeros_like(phase_bins)
        y_err = np.ones_like(phase_bins)
        #self.li, = self.ax.plot(phase_bins,sigma_array, 'bo')
        #errorbar(x+0.5,best_sigma_array,xerr=x_err,yerr=y_err,color='red',ecolor='black',fmt='o')
        self.container = self.ax.errorbar(phase_bins,sigma_array,xerr=x_err,yerr=y_err,color='red',ecolor='black',fmt='o')
        self.draw_count += 1 
        self.ax.set_title("Power vs Phase: draw_count={0:d}".format(self.draw_count))
        self.ax.set_xlabel("Phase")
        self.ax.set_ylabel("S/N")
        self.ax.grid()
        self.fig.canvas.draw()
        plot.show(block=False)
        print("   Leaving initPlot()")
        return 
        
    def updatePlot(self,args) :  
        print("Entering updatePlot()") 
        nRecords, short_times, short_series = self.getData()
        phase_hist = self.anaPulsar(short_times,short_series)
        phase_bins = np.linspace(0.,1.,self.nPhaseBins)
        #self.li, = self.ax.plot(phase_bins,phase_hist, 'bo')
        yMin, yMax = np.min(phase_hist), np.max(phase_hist)
        sigma_array = self.getSigmaArray(phase_hist)
        best_sigma = max(sigma_array)
        yMin, yMax = -4., max(4.,np.max(sigma_array)) 
        dy = yMax - yMin
        self.ax.set_ylim(yMin-0.1*dy,yMax+0.1*dy) 
        if 'container' in locals() and self.container is not None : self.container.remove() 
        self.container.lines[0].set_data(phase_bins, sigma_array)
        x_err = np.zeros_like(phase_bins)
        y_err = np.ones_like(phase_bins)
        self.container.remove()
        self.container = self.ax.errorbar(phase_bins,sigma_array,xerr=x_err,yerr=y_err,color='red',ecolor='black',fmt='o')
        self.draw_count += 1 
        if len(short_times) > 0 : self.t0 = short_times[0]
        self.ax.set_title("Power vs Phase: draw_count={0:d}  t={1:.1f} s".format(self.draw_count,self.t0))
        self.fig.canvas.draw()
        self.draw_count += 1 
        plot.pause(0.1)
        print("   Leaving updatePlot()")
        return 
            
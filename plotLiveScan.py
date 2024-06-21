import numpy as np 
import matplotlib.pyplot as plot
import time
import glob
from DAQ import DAQ
import sys 
import signal 

class plotScan() :

    def __init__(self,args):
        self.fft_size = args.fft_size 
        self.dt = args.decimation_factor*args.fft_size/args.samp_rate

        self.f = open("data_1.raw",'rb')	                # Open the file to be read
        
        self.count = 0
        self.tSample = []
        self.power = []
        self.calibration = 34.6
        self.printOn = args.printOn
        
    def getData(self) :
        if self.printOn : print("Entering plotLiveScan.getData()")
        nRecords = 0 
        
        while True :	
            data = np.fromfile(self.f, dtype=np.float32, count=self.fft_size)
            if len(data) < self.fft_size : break 
            nRecords += 1
            self.count += 1  
            self.tSample.append(self.count*self.dt)    
            self.power.append(self.calibration*np.sum(data))
            
        if self.printOn : print("In plotLiveScan.getData() nRecords={0:d} count={1:d} t={2:.1f}".format(
            nRecords,self.count,self.count*self.dt))
        return nRecords
            
    def initPlot(self,args):

        if self.printOn : print("Entering plotLiveScan.initPlot()")
        # Plot total power vs. time
        self.fig = plot.figure(figsize=(12, 10), dpi=80)
        self.ax = self.fig.add_subplot(111)
        axx = self.ax
        for item in ([axx.title, axx.xaxis.label, axx.yaxis.label] + axx.get_xticklabels() + axx.get_yticklabels()):
            item.set_fontsize(20)
        nRecords = self.getData()
        self.li, = self.ax.plot([], [], 'b.')
        self.ax.set_title("Power vs. Time",fontsize=20)
        self.ax.set_xlabel("t (s)",fontsize=20)
        self.ax.set_ylabel("Power (K)",fontsize=20)
        self.ax.grid()
        self.fig.canvas.manager.set_window_title('plotLiveScan.py')
        self.fig.canvas.draw()
        if self.printOn : print("In plotLiveScan.initPlot() before show()")
        plot.show(block=False)

    def getTimeLimits(self, t) :
        tScales = [10., 20., 50., 100., 200., 500., 1000., 2000., 5000., 10000., 20000., 50000., 100000.]
        tMax = t[len(t)-1]
        for tScale in tScales :
            if tMax < tScale :return [0., tScale]
        return [0., tMax]

    def getPowerLimits(self, power) :
        powerScales = [10., 20., 50., 100., 200., 500., 1000., 2000., 5000., 10000.] 
        pMax = np.amax(power)
        return [0., 1.1*pMax]

    def plotNewSeries(self,args) :
        if self.printOn : print("Entering plotLiveScan.plotNewSeries()")
        nRecords = self.getData()
        ts, p = np.array(self.tSample), np.array(self.power)   
        self.ax.set_xlim(self.getTimeLimits(ts)) 
        self.ax.set_ylim(self.getPowerLimits(p)) 
        self.li.set_xdata(ts) 
        self.li.set_ydata(p)
        self.fig.canvas.draw()
        plot.pause(0.1)
        return
    
def signal_handler(sig, frame):
    print('Cntl+C pressed . . . stopping flowgraph')
    tb.blocks_head_0.set_length(0)
    time.sleep(1)
    sys.exit(0)

def getArgs() :
    import argparse 
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--printOn",action="store_true",help="Turn on printing")
    parser.add_argument("--f_center",type=float,default=1.418e9,help="Center frequency")
    parser.add_argument("--samp_rate",type=float,default=1.0e7,help="USRP sample rate.")
    parser.add_argument("--fft_size",type=int,default=2048,help="FFT size")
    parser.add_argument("--decimation_factor",type=int,default=10000,help="Decimation factor")
    parser.add_argument("-m","--maxRecords",type=int,default=10000,help="Maximum number of records to plot.")
    parser.add_argument("--static",action="store_true",help="Static plot")
    return parser.parse_args()

# execution starts here
# start the DAQ running, but don't bother with metadata or with permanently saving the output

args = getArgs()
printOn = args.printOn 
f = args.f_center 
tb = DAQ(base_name="data", f1=f, f2=f, fft_size=args.fft_size, decimation_factor=args.decimation_factor, 
         samp_rate=args.samp_rate)
if printOn : 
    print("Top block instantiated.")
    print("Starting DAQ flowgraph")

tb.start()

# wait for DAQ to start 
print("In plotLiveScan.py.  Waiting for DAQ to start.")
time.sleep(2.0)

# this allows one to gracefully exit with Cntl+C 
print("\nRunning for 3600 seconds.  Press Cntl+C to exit.") 
signal.signal(signal.SIGINT, signal_handler)

#start the plotting process
ps = plotScan(args)
ps.initPlot(args)

while True :
    ps.plotNewSeries(args)         
    time.sleep(2.0)

#tb.wait()
#print("Flow stopped naturally after running for {0:d} seconds.".format(args.run_time))
#sys.exit(0)




    


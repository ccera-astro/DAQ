import numpy
import sys
import time
import os
import glob
import argparse
import plotScan
from math import sin, cos, acos, radians, degrees

def getArgs() :
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--printLevel",type=int,help="Print level.")
    parser.add_argument("-k","--keyword",help="Keyword, e.g., sunScan.")
    parser.add_argument("-o","--outFile",default="scan",help="Output file name.")
    parser.add_argument("-m","--maxRecords",type=int,default=10000,help="Maximum number of records to plot.")
    parser.add_argument("-t","--testMode",action="store_true",help="Test mode.")
    parser.add_argument("--static",action="store_true",help="Static plot")
    parser.add_argument("--noiseLeader",action="store_true",help="Add noise pulse leader.") 
    return parser.parse_args()

def setupRadio(args) :
    if args.testMode : return 
    print "\nSetting up radio."
    os.system('rxcntl off > rxcntl.log')
    os.system('rxcntl cha on > rxcntl.log')
    os.system('rxcntl cha 21cm > rxcntl.log')
    os.system('rxcntl chb on > rxcntl.log')
    os.system('rxcntl chb 21cm > rxcntl.log')
    os.system('rxcntl noise off > rxcntl.log')

def startDAQ(args) :
    if args.testMode : return
    os.system('echo GO > GO')
    import top_block_ex  
    tb = top_block_ex.top_block(freq=1420000000)
    tb.start()
    startTime = time.time()
    time.sleep(5.) 
    return tb

def stopDAQ(tb,args) :
    if args.testMode : return
    print "Data taking interrupted.  Begin shutdown ..."
    tb.stop()

def generateNoisePulse(args) :
    if args.testMode : return
    print "Turning noise on."
    os.system('rxcntl noise on > rxcntl.log')
    time.sleep(10.)
    print "Turning noise off."
    os.system('rxcntl noise off > rxcntl.log')

#
# execution starts here
#

args = getArgs()
setupRadio(args)
DAQ = startDAQ(args)

time.sleep(1.0)
if args.noiseLeader : generateNoisePulse(args)

#start the plotting process
ps = plotScan.plotScan()
ps.initPlot(args)

while True :
    if len(glob.glob('GO')) > 0 :
        time.sleep(0.5)
        ps.plotNewSeries(args)         
    else :
        stopDAQ(DAQ,args)
        ps.writeOutFiles(args) 
        print "Program exiting."
        exit()

    






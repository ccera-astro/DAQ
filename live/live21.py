import numpy
#import matplotlib.pyplot as plot
import sys
import time
import os
import subprocess
import shutil
import glob
import argparse
import plot21
from math import sin, cos, acos, radians, degrees

def getArgs() :
    parser = argparse.ArgumentParser()
    parser.add_argument("-p","--printLevel",type=int,help="Print level.")
    parser.add_argument("-a","--alpha",type=float,default=-1.,help="Averaging alpha.")
    parser.add_argument("-k","--keyword",help="Keyword, e.g., sunScan.")
    parser.add_argument("-m","--maxRecords",type=int,default=10000,help="Maximum number of records to plot.")
    parser.add_argument("-t","--testMode",action="store_true",help="Test mode.")
    parser.add_argument("--static",action="store_true",help="Static plot")
    parser.add_argument("--noNotch",action="store_true",help="Disable notch filter.")
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
    tb = top_block_ex.top_block()
    tb.start()
    startTime = time.time()
    time.sleep(5.) 
    return tb

def stopDAQ(tb,args,fOutPos) :
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


def getAlpha(args,lastTime,lastUVW) :
    alpha = args.alpha
    if args.alpha < 1. : return args.alpha, lastTime, lastUVW
    try:
        line = open('/tmp/fuse/pos','r').read()
        now = float(line.split()[0])
        if now - lastTime > 5. :
            tht = radians(90. - float(line.split()[1])) 
            cs, sn = cos(tht), sin(tht)
            phi = radians(float(line.split()[2]))
            UVW = [sn*cos(phi), sn*sin(phi), cs]
            angle = degrees(acos(lastUVW[0]*UVW[0]  + lastUVW[1]*UVW[1] + lastUVW[2]*UVW[2]))
            if angle > 1. :    # dish is moving
                return 0.2, now, UVW
            else :
                return 0.01, now, UVW
    except:
        print("In live21.getAlpha():  /tmp/fuse/pos file not found")
        return args.alpha, lastTime, lastUVW
    
#
# execution starts here
#

args = getArgs()
ttime, UVW = 0, [0., 0., -1.]
setupRadio(args)
DAQ = startDAQ(args)

#start the plotting process
l21 = plot21.plot21()
l21.initPlot(args)


while True :
    if len(glob.glob('GO')) > 0 :
        #time.sleep(1.0)
        alpha, ttime, UVW = getAlpha(args,ttime,UVW)
        l21.plotNewSpectrum(args,alpha)         
    
    else :
        stopDAQ(DAQ,args,fOutPos) 
        print "Program exiting."
        exit()

    






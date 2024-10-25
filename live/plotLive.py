import json 
import glob
import argparse
import plotDoppler
from math import sin, cos, acos, radians, degrees
import time 
import socket 
from pathlib import Path 

def getArgs() :
    parser = argparse.ArgumentParser()
    parser.add_argument("-b","--base_name",default=None,help="Base name.")
    parser.add_argument("-d","--data_dir",default=None,help="Data directory.")
    parser.add_argument("-p","--printLevel",type=int,help="Print level.")
    parser.add_argument("-a","--alpha",type=float,default=-1.,help="Averaging alpha.")
    parser.add_argument("--static",action="store_true",help="Static plot")
    parser.add_argument("--sun_mode",action="store_true",help="Sun mode")
    parser.add_argument("--noNotch",action="store_true",help="Disable notch filter.")
    return parser.parse_args()

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
    
# the default is to display data from the last file on the list
# which is the one currently being written 
def getBaseName(args) :
    if not args.data_dir :
        data_dir = "/mnt/c/Users/marlow/Documents/CCERA/data/" 
        if "receiver" in socket.gethostname().lower() : data_dir = str(Path.home()) + "/data/" 
    else :
        data_dir = args.data_dir 
    
    if not args.base_name :
        s = data_dir + "*.json"
        files = glob.glob(s)
        #print("In getBaseName() before sort: files={0:s}".format(str(files)))
        sorted_files = sorted(files)
        #print("\n\nIn getBaseName() after sort: files={0:s}".format(str(sorted_files)))
        base_name = sorted_files[-1].strip(".json")
    else :
        base_name = data_dir + args.base_name
    
    print("In getBaseName() : base_name={0:s}".format(base_name))
    return base_name
    
# execution starts here

args = getArgs()
base_name = getBaseName(args)
ttime, UVW = 0, [0., 0., -1.]

# read JSON file to determine type of run 
with open(base_name + ".json") as json_file : metadata = json.load(json_file)

# determine the run mode and start the plotting process 
if metadata["run_mode"].lower() == "doppler" :
    print("Starting plotDoppler: base_name={0:s}".format(base_name))
    file_name = base_name + "_1.raw"
    pd = plotDoppler.plotDoppler(file_name,metadata)
    pd.initPlot(args)
else :
    print("run_mode={0:s} not implented . . . exiting.")
    exit() 

while True :
    #alpha, ttime, UVW = getAlpha(args,ttime,UVW)
    alpha = 0.5 
    pd.plotNewSpectrum(args,alpha)      
    time.sleep(1.0)
    






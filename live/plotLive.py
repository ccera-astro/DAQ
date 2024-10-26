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

def getAzAlt() :
    import xmlrpc.client as xml
    rpc = xml.ServerProxy("http://172.22.121.35:9090")
    try :
        values = rpc.query_both_axes()
        alt, az = values[0],values[1]
        az_rate, alt_rate = rpc.query_az_rate(), rpc.query_el_rate() 
        return az, alt, az_rate, alt_rate
    except OSError :
        print("In plotLive.getAzAlt(): OSError rpc server not found.")
        return 0., 90., 0., 0. 
    
def getAlpha(args,lastUVW) :
    if args.alpha < 1. : return args.alpha, lastUVW
    az, alt, az_rate, alt_rate = getAzAlt()
    tht = radians(90. - alt) 
    cs, sn = cos(tht), sin(tht)
    phi = radians(az)
    UVW = [sn*cos(phi), sn*sin(phi), cs]
    angle = degrees(acos(lastUVW[0]*UVW[0]  + lastUVW[1]*UVW[1] + lastUVW[2]*UVW[2]))
    if angle > 1. : return 0.2, UVW
    else : return 0.01, UVW
    
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
UVW = [0., 0., -1.]

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
    alpha, UVW = getAlpha(args,UVW)
    pd.plotNewSpectrum(args,alpha)      
    time.sleep(10.0)
    






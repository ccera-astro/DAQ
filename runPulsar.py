# run Pulsar flowgraph 
from DAQ import DAQ
import time 
import json
import sys 
import signal

def getArgs() :
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--f_center",type=float,default=1413.5e6,help="Center frequency")
    parser.add_argument("--samp_rate",type=float,default=2.5e7,help="USRP sample rate.")
    parser.add_argument("--fft_size",type=int,default=32,help="FFT size")
    parser.add_argument("--decimation_factor",type=int,default=250,help="Decimation factor")
    parser.add_argument("--run_type",default='Track',help="Track or Transit")
    parser.add_argument("--dir",default="/home/dmarlow/data/",help="Data directory")
    parser.add_argument("--run_time",type=int,default=600,help="Run time in seconds.")
    parser.add_argument("--printOn",action="store_true",help="Turn on print statements")
    return parser.parse_args()

def getAzAlt() :
    import xmlrpc.client as xml
    rpc = xml.ServerProxy("http://172.22.121.35:9090")
    values = rpc.query_both_axes()
    az, alt = values[0],values[1]
    return az, alt

#   build meta data dictionary 
def buildMetadata(args,tb) :
    dict = {}
    dict['freq'] = tb.get_f1() 
    dict['srate'] = srate = tb.get_samp_rate() 
    dict['fft_size'] = fft_size = tb.get_fft_size()
    N = tb.get_decimation_factor() 
    dict['t_sample'] = 1./(srate/fft_size/N)
    dict['n_chans'] = 2
    dict['run_type'] = args.run_type 
    az, alt = getAzAlt()
    dict['az'] = az
    dict['alt'] = alt
    return dict 
    
#   write metadata out JSON file 
def writeMetadata(metadata,file_base_name) :
    file_name = file_base_name + '.json'
    with open(file_name, 'w') as fp :
        json.dump(metadata, fp)

def signal_handler(sig, frame):
    print('Cntl+C pressed . . . stopping flowgraph')
    tb.blocks_head_0.set_length(0)
    time.sleep(1)
    sys.exit(0)

# begin execution

args = getArgs() 
printOn = args.printOn 

dir = args.dir 
file_base_name = dir + time.strftime("%Y-%m-%d-%H%M", time.gmtime())

print("Entering runPulsar: file_base_name={0:s}".format(file_base_name))

tb = DAQ(base_name=file_base_name, seconds=args.run_time, f1=1.4204e9, f2=1.4204e9, 
         fft_size=args.fft_size, decimation_factor=args.decimation_factor, samp_rate=args.samp_rate)

if printOn : print("Top block instantiated.")

metadata = buildMetadata(args,tb)

if printOn : print("Metadata built.  metadata={0:s}".format(str(metadata)))

#t0 = time.time() 
print("Starting Pulsar flowgraph")
tb.start()

# let the flowgraph run a short time so allow the time stamp file to be written 
time.sleep(2)
metadata['t_start'] = float(open(file_base_name+"_ts.txt").readline()) 
writeMetadata(metadata,file_base_name)

# this allows one to gracefully exit with Cntl+C 
signal.signal(signal.SIGINT, signal_handler)
print("\nRunning for {0:d} seconds.  Press Cntl+C to exit.".format(args.run_time)) 

tb.wait()
print("Flow stopped naturally after running for {0:d} seconds.".format(args.run_time))
sys.exit(0)





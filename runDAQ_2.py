# run flowgraph 
from DAQ import DAQ
import time 
import json
import sys 
import signal
from math import degrees
import ephem 
import numpy as np 
import os 

def getArgs() :
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r","--run_mode",default="none",help="Run mode: pulsar, doppler, scan, or generic")
    parser.add_argument("--f_center",type=float,default=-1.,help="Center frequency")
    parser.add_argument("--samp_rate",type=float,default=-1.,help="USRP sample rate.")
    parser.add_argument("--fft_size",type=int,default=-1,help="FFT size")
    parser.add_argument("--decimation_factor",type=int,default=-1,help="Decimation factor")
    parser.add_argument("--run_type",default='Transit',help="Track or Transit")
    parser.add_argument("--target",default='none',help="Target, e.g. J0332+5434")
    parser.add_argument("--dir",default="/home/dmarlow/data/",help="Data directory")
    parser.add_argument("--run_time",type=int,default=600,help="Run time in seconds.")
    parser.add_argument("--printOn",action="store_true",help="Turn on print statements")
    parser.add_argument("--lmst",type=float,default=None,help="Wait for this lmst before starting.")
    parser.add_argument("--n_jobs",type=int,default=1,help="Number of jobs to run.")
    parser.add_argument("--no_avg",action="store_true",help="Don't make an .avg file")
    parser.add_argument("--no_sum",action="store_true",help="Don't make a .sum file")
    parser.add_argument("--XMLRPC",action="store_true",help="Enable XMLRPC control")
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
        print("In runDAQ.getAzAlt(): OSError rpc server not found.")
        return 0., 90., 0., 0. 
    
def getObserver(observatory) :
    obs=ephem.Observer()
    if observatory.lower() == 'belmar' :
        obs.lat='40.184693'
        obs.lon='-74.056116'
    elif observatory.lower() == 'jadwin' :
        obs.lat='40.34488'
        obs.lon='-74.65155'
    elif observatory.lower() == 'carp' :
        obs.lat='45.35025'
        obs.lon='-76.05609'
    else :
        print("ERROR in getObserver.  No observatory called {0:s}.  Exiting".format(observatory))
        exit() 
    return obs

def H2E(obs, dAz, dAl) :
    (RA, dec) = obs.radec_of(str(dAz),str(dAl))
    RA_deg = degrees(RA)
    if RA_deg > 180. : RA_deg -= 360.
    return RA_deg, degrees(float(dec))

def E2G( RA, dec) :
    RA_hours = RA/15.
    eCoords = ephem.Equatorial(str(RA_hours),str(dec))
    gCoords = ephem.Galactic(eCoords)
    return degrees(gCoords.lon), degrees(gCoords.lat)

#   build meta data dictionary 
def buildMetadata(run_mode,target,tb) :
    dict = {}
    dict['freq'] = tb.get_frequency() 
    dict['srate'] = srate = tb.get_samp_rate() 
    dict['fft_size'] = fft_size = tb.get_fft_size()
    N = tb.get_decimation_factor() 
    dict['decimation_factor'] = N 
    dict['t_sample'] = 1./(srate/fft_size/N)
    dict['n_chans'] = 2
    dict['run_mode'] = run_mode  
    dict['target'] = target 
    az, alt, az_rate, alt_rate = getAzAlt()
    dict['az'] = az
    dict['alt'] = alt
    dict['run_type'] = 'Transit'
    if abs(az_rate) > 0.001 or abs(alt_rate) > 0.001 : dict['run_type'] = "Track"
    carp = getObserver("carp")
    dict['RA'], dict['dec'] = H2E(carp,az,alt)
    dict['gLon'], dict['gLat'] = E2G(dict['RA'],dict['dec'])
    return dict 
    
#   write metadata out JSON file 
def writeMetadata(metadata,file_base_name) :
    file_name = file_base_name + '.json'
    with open(file_name, 'w') as fp :
        json.dump(metadata, fp)
    return

def endRun(metadata,file_base_name) :
    metadata["run_time"] = time.time() - metadata["t_start"]
    writeMetadata(metadata,file_base_name)
    print("Run ended.  Metadata for {0:s}".format(file_base_name))
    for key, value in metadata.items(): print("{0:>20} : {1:s}".format(str(key),str(value)))
    return

def signal_handler(sig, frame):
    print('Cntl+C pressed . . . stopping flowgraph')
    tb.blocks_head_0.set_length(0)
    time.sleep(1)
    endRun(metadata,file_base_name)
    sys.exit(0)

def set_filename(file_name) :
    print("Enter set_filename() file_name={0:s}".format(file_name))
    file_base_name = tb.get_base_name() 
    print("   Present file_base_name={0:s}".format(file_base_name))
    # At beginning of move position system changes output file to /dev/null
    # When the move is complete, the file is set a non-null value
    try :
        
        if file_name == "/dev/null" :       
            import json
            with open(file_base_name + ".json") as json_file : metadata = json.load(json_file)
            print("   metadata loaded")
            tb.set_base_name("data")
            metadata["run_time"] = time.time() - metadata["t_start"]
            writeMetadata(metadata,file_base_name)
            print("   base_name set to /dev/null")
        else :
            print("   Changing file_name to {0:s}".format(file_name))
            metadata = buildMetadata('doppler','galactic_scan',tb)
            metadata['t_start'] = time.time()    # this will not be as precise as time_catcher() but should be OK
            file_base_name = args.dir + time.strftime("%Y-%m-%d-%H%M", time.gmtime())
            writeMetadata(metadata,file_base_name)
            tb.set_base_name(file_base_name)
            print("   base_name set to {0:s}".format(file_base_name))
        return True
    except :
        print("Exception in set_filename() ignored")
        return False 

def cur_sidereal(longitude):
    longstr = "%02d" % int(longitude)
    longstr = longstr + ":"
    longitude = abs(longitude)
    frac = longitude - int(longitude)
    frac *= 60
    mins = int(frac)
    longstr += "%02d" % mins
    longstr += ":00"
    x = ephem.Observer()
    x.date = ephem.now()
    x.long = longstr
    jdate = ephem.julian_date(x)
    tokens=str(x.sidereal_time()).split(":")
    hours=int(tokens[0])
    minutes=int(tokens[1])
    seconds=int(float(tokens[2]))
    sidt = "%02d,%02d,%02d" % (hours, minutes, seconds)
    return (sidt)

def lmst_wait(target_lmst) :
    ONEMINUTE = 60.0/3600.0
    carp = getObserver("carp")
    longitude = degrees(carp.lon) 
    x = cur_sidereal(longitude)
    while True:
        x = cur_sidereal(longitude)
        x = x.split(",")
        lmst = float(x[0])
        lmst += float(x[1])/60.0
        lmst += float(x[2])/3600.0
        print("In runDAQ.lmst_wait() current lmst={0:.3f} target lmst={1:.3f}".format(lmst,target_lmst))
        if (lmst >= target_lmst and lmst <= (target_lmst + ONEMINUTE)):
            break
        time.sleep(20.0)

def getData(file,fft_size) :
    print("Reading from file: {0:s}".format(file))
    vals = np.fromfile(file, dtype=np.float32)
    cols = fft_size
    rows = int(len(vals)/fft_size)
    vals = np.reshape(vals, (rows,cols))   
    return vals, rows, cols

# convert .raw data format to .sum data format by summing over columns in the 
# data array to make a time series of single values 
def makeSumFile(base_name, metadata) :

    with open(base_name + ".json") as json_file : metadata = json.load(json_file)

    fft_size = metadata['fft_size']

    for chan in [1,2] :
        file = base_name + "_{0:d}.raw".format(chan)
        data, nRows, nCols = getData(file,fft_size)
        print("Read {0:d} {1:d}-channel spectra from {2:s}".format(nRows,nCols,file))
        power = np.sum(data,1)
        file_out = base_name + "_{0:d}.sum".format(chan)
        with open(file_out,'w') as file : power.tofile(file)

def makeAverageFile(base_name, metadata) :
    fft_size = metadata['fft_size']

    for chan in [1,2] :
        data, rows, cols = getData(base_name + "_{0:d}.raw".format(chan),fft_size)
        print("After getData Chan {0:d}: rows={1:d} cols={2:d}".format(chan,rows,cols))

        # reshape array into a series of row 
        data = np.reshape(data, (rows,cols))   
        print("len(data[0])={0:d}".format(len(data[0])))

        avg_data = np.mean(data,0)
        print("len(avg_data)={0:d}".format(len(avg_data)))

        avg_data.tofile(base_name + "_{0:d}.avg".format(chan))

# begin execution

args = getArgs() 
printOn = args.printOn 
run_mode = args.run_mode.lower() 

f_clock = 1.25e8 
if run_mode == "pulsar" :
    f1, f2 = 1.4204e9, 1.4204e9
    fft_size = 32
    decimation_factor = 250
    samp_rate = f_clock/6.  
elif run_mode == "doppler" :
    f1, f2 = 1.4204e9, 1.4204e9
    fft_size = 2048
    decimation_factor = 10000
    samp_rate = f_clock/30. 
elif run_mode == "scan" :
    f1, f2 = 1.4185e9, 1.4185e9
    fft_size = 2048
    decimation_factor = 10000
    samp_rate = f_clock/14. 
elif run_mode == "generic" :
    f1, f2 = 1.4204e9, 1.4204e9
    fft_size = 2048
    decimation_factor = 10000
    samp_rate = f_clock/20. 
else :
    print("**ERROR** invalid run_mode={0:s} ***Exiting***".format(run_mode))
    exit()

# non-negative user parameters can override default parameters for the specified mode
if args.f_center > 0. : f1, f2 = args.f_center, args.f_center 
if args.fft_size > 0 : fft_size = args.fft_size 
if args.decimation_factor > 0 : decimation_factor = args.decimation_factor
if args.samp_rate > 0. : samp_rate = args.samp_rate  

if args.lmst != None : 
    print("Waiting for lmst={0:.2f}".format(args.lmst))
    lmst_wait(args.lmst)
    print("Starting")

# set up XMLRPC server so as to listen to control messages from 
# the positioning system.   Create and run the XML server in a 
# separate thread

if args.XMLRPC :
    from xmlrpc.server import SimpleXMLRPCServer
    import threading
    xmlserver = SimpleXMLRPCServer(('0.0.0.0', 14200), allow_none=True, logRequests=False)
    xmlserver.register_function(set_filename)
    server_thread = threading.Thread(target=xmlserver.serve_forever)
    server_thread.daemon = True
    server_thread.start()

# allow for the possibility of a chain of jobs
for i in range(args.n_jobs) :

    file_base_name = args.dir + time.strftime("%Y-%m-%d-%H%M", time.gmtime())

    print("In runDAQ: Run mode={0:s} file_base_name={1:s} {2:d} of {3:d}".format(
    run_mode,file_base_name,i,args.n_jobs))

    try :
        tb = DAQ(base_name=file_base_name, seconds=args.run_time, frequency=f1,  
            fft_size=fft_size, decimation_factor=decimation_factor, samp_rate=samp_rate)
    except :
        print("Error instantiating top_block.  Wait 10 seconds and try again.")
        time.sleep(10.)
        continue

    if printOn : print("Top block instantiated.")

    metadata = buildMetadata(args.run_mode,args.target,tb)

    if printOn : print("Metadata built.  metadata={0:s}".format(str(metadata)))

    print("Starting {0:s} flowgraph".format(run_mode))
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
    endRun(metadata,file_base_name)

    if (run_mode == "pulsar" or run_mode == "scan") and not args.no_sum : makeSumFile(file_base_name, metadata)
    if run_mode == "doppler" and not args.no_avg : 
        makeAverageFile(file_base_name, metadata)
        os.system("rm {0:s}_1.raw".format(file_base_name))
        os.system("rm {0:s}_2.raw".format(file_base_name))

    del tb
    if args.n_jobs > 1 : time.sleep(10.)

sys.exit(0)





import NumatoGPIO 
from argparse import ArgumentParser 
from time import sleep, time, strftime, gmtime, time   
from DAQ import DAQ 
import json 

#   build meta data dictionary 
def buildMetadata(run_mode,target,tb) :
    dict = {}
    dict['freq'] = tb.get_frequency() 
    dict['srate'] = srate = tb.get_samp_rate() 
    dict['fft_size'] = fft_size = tb.get_fft_size()
    N = tb.get_decimation_factor() 
    dict['decimation_factor'] = N 
    dict['t_sample'] = 1./(srate/fft_size/N)
    dict['n_chans'] = 1
    dict['run_mode'] = run_mode  
    dict['target'] = target 
    dict['run_type'] = 'Transit'
    dict['t_start'] = time()
    return dict 

#   write metadata out JSON file 
def writeMetadata(metadata,file_base_name) :
    file_name = file_base_name + '.json'
    with open(file_name, 'w') as fp :
        json.dump(metadata, fp)
    return
    
# begin execution here 
parser = ArgumentParser()
parser.add_argument("--device", type=str, default="/dev/ttyACM0", help="GPIO device")
parser.add_argument("--timeout", type=float, default=0.050, help="Read timeout")
parser.add_argument("--run_time",type=int,default=120,help="run time in seconds")
parser.add_argument("--dwell_time",type=int,default=10,help="dwell time in seconds")
args = parser.parse_args()

GPIO = NumatoGPIO.NumatoGPIO(args.device,timeout=args.timeout)
f_clock, f1, fft_size, decimation_factor = 1.6e7, 1.4204e9, 2048, 10000
samp_rate = f_clock/4 
dir_name = "/home/student/data/RA_camp/"
nTries = 0 
file_base_name = dir_name + "Ch00_" + strftime("%Y-%m-%d-%H%M%S", gmtime())
run_time = args.run_time 
start_time = time() 
while nTries < 10 :
    nTries += 1 
    try :
        print("Instantiating top_block: file={0:s}".format(file_base_name))
        tb = DAQ(base_name=file_base_name, seconds=run_time)
        break 
    except: 
        print("Error instantiating top_block.  Wait 10 seconds and try again.")
        sleep(10.)
        continue

print("Top block instantiated after {0:d} trial(s).".format(nTries))
metadata = buildMetadata("doppler","RA_camp",tb)
print("Metadata built.") 
writeMetadata(metadata,file_base_name)

# Set up GPIO 
GPIO = GPIO 
GPIO_good = GPIO.connect() 
if GPIO_good : print("GPIO connection established.") 
else : print("***ERROR GPIO serial connection failed.****")

channel = 0 
tb.start() 
print("top_block started")

while True :
    sleep(args.dwell_time)
    elapsed_time = time() - start_time
    print("Elapsed time = {0:.2f} Time remaining={1:.2f}".format(elapsed_time,args.run_time-elapsed_time)) 
    if elapsed_time > args.run_time :
        print("Total time expired ... exiting")
        break
    # set file name to null, change MUX, and then set file name to new channel 
    tb.set_base_name("temp")
    channel = (channel+1) % 2
    #update channel select hardware
    if GPIO_good : GPIO.write_all_outputs(channel)
    sleep(1.)
    ch = "Ch{0:02d}_".format(channel)
    file_base_name = dir_name + ch + strftime("%Y-%m-%d-%H%M%S", gmtime())
    tb.set_base_name(file_base_name)
    metadata['t_start'] = time() 
    writeMetadata(metadata,file_base_name)
    print("New file: {0:s}".format(file_base_name))

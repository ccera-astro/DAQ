from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QCheckBox, QGridLayout, QPushButton, QLabel, QDoubleSpinBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import LED 
import NumatoGPIO 
from argparse import ArgumentParser 
from time import sleep, time, strftime, gmtime, time   
from DAQ import DAQ 
import json 
import numpy as np 

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

    chan = 1 
    file = base_name + "_{0:d}.raw".format(chan)
    data, nRows, nCols = getData(file,fft_size)
    print("Read {0:d} {1:d}-channel spectra from {2:s}".format(nRows,nCols,file))
    power = np.sum(data,1)
    print("len(data)={0:d} len(power)={1:d} data.shape={2}".format(len(data)),len(power),data.shape) 
    file_out = base_name + "_{0:d}.sum".format(chan)
    with open(file_out,'w') as file : power.tofile(file)
    
class MainWindow(QMainWindow):
    def __init__(self,args,GPIO):
        super().__init__()
        self.setWindowTitle("MUX Controller")

        # Setup DAQ
        f_clock, f1, fft_size = 1.6e7, 1.4204e9, args.fft_size
        samp_rate = f_clock/4 
        decimation_factor = int(samp_rate/fft_size)  
        self.dir_name = "/home/student/data/RA_camp/"
        nTries = 0 
        self.file_base_name = self.dir_name + "Ch00_" + strftime("%Y-%m-%d-%H%M%S", gmtime())
        self.run_time = args.run_time 
        
        while nTries < 10 :
            nTries += 1 
            try :
                #self.tb = DAQ(base_name=self.file_base_name, seconds=1000000, frequency=f1,  
                #    fft_size=fft_size, decimation_factor=decimation_factor, samp_rate=samp_rate, mclock=f_clock,
                #    refclock="internal",pps="internal",subdev="A:A A:B",device="type=b200,num_recv_frames=256")
                print("Before instantiating top_block: file={0:s}".format(self.file_base_name))
                self.tb = DAQ(base_name=self.file_base_name, seconds=self.run_time, fft_size=fft_size,
                              decimation_factor=decimation_factor)
                break 
            except: 
                print("Error instantiating top_block.  Wait 10 seconds and try again.")
                sleep(10.)
                continue

        print("Top block instantiated after {0:d} trial(s).".format(nTries))
        self.metadata = buildMetadata("doppler","RA_camp",self.tb)
        self.start_time = time() 
        print("Metadata built.") 

        # Set up GPIO 
        self.GPIO = GPIO 
        self.GPIO_good = GPIO.connect() 
        if not self.GPIO_good : print("***ERROR GPIO serial connection failed.****")

        self.n_channels = 8 
        self.channel = 0
        layout = QGridLayout()
        self.LEDs, self.CBs = [], [] 
        for i in range(self.n_channels) :
            self.LEDs.append(LED.LED(color="red",on=False))  
            self.CBs.append(QCheckBox("Channel {0:d}".format(i+1)))
            self.CBs[i].setFont(QFont("Arial",12))
            layout.addWidget(self.LEDs[i],i,0)  
            layout.addWidget(self.CBs[i],i,1)

        self.RunLabel = QLabel("Stopped")
        self.RunLabel.setAlignment(Qt.AlignCenter)
        self.RunLabel.setFont(QFont("Arial",14))
        self.RunLabel.setStyleSheet("color: red;")
        layout.addWidget(self.RunLabel,0,2)
        self.StartButton = QPushButton("Start")
        self.StartButton.setFont(QFont("Arial",14))
        layout.addWidget(self.StartButton,1,2)
        self.StartButton.clicked.connect(self.start_clicked)
        self.StopButton = QPushButton("Stop") 
        self.StopButton.setFont(QFont("Arial",14))
        self.StopButton.clicked.connect(self.stop_clicked)
        layout.addWidget(self.StopButton,2,2)
        self.CBs[self.channel].setChecked(True)
        self.LEDs[self.channel].set_on(True)

        self.dwell_time_label = QLabel("Dwell time(s)")
        self.dwell_time_label.setFont(QFont("Arial",14))
        layout.addWidget(self.dwell_time_label,3,2)
        self.dwell_time_spinner = QDoubleSpinBox()
        self.dwell_time_spinner.setRange(0.0, 600.0)
        self.dwell_time_spinner.setSingleStep(1.)
        self.dwell_time_spinner.setDecimals(1)
        self.dwell_time_spinner.setValue(args.dwell_time)
        self.dwell_time_ms = int(1000*self.dwell_time_spinner.value())
        self.dwell_time_spinner.valueChanged.connect(self.dwell_time_changed)
        layout.addWidget(self.dwell_time_spinner,4,2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_channel)

    def update_channel(self) :
        
        elapsed_time = time() - self.start_time
        print("Update channel: elapsed_time={0:.2f} time remaining={1:.2f}".format(
            elapsed_time,self.run_time-elapsed_time))
        if elapsed_time > self.run_time :
            print("Run time exceeded . . . stopping") 
            self.stop_clicked() 
            return 
            
        old_chan = self.channel 
        iMax = self.channel + self.n_channels + 1 
        new_chan = 0 
        for i in range(self.channel+1,iMax) :
            j = i % self.n_channels 
            if self.CBs[j].checkState() > 0 : 
                new_chan = j
                break 

        # no action is required if there is no change in channel 
        if new_chan == old_chan : return 

        # set file name to null, change MUX, and then set file name to new channel 
        self.tb.set_base_name("temp")
        writeMetadata(self.metadata,self.file_base_name)
        makeSumFile(self.file_base_name, self.metadata)
        sleep(1.)
        self.LEDs[self.channel].set_on(False)
        self.channel = new_chan 
        self.LEDs[self.channel].set_on(True)
        #update channel select hardware
        if self.GPIO_good : GPIO.write_all_outputs(self.channel)
        sleep(2.)
        ch = "Ch{0:02d}_".format(self.channel)
        self.file_base_name = self.dir_name + ch + strftime("%Y-%m-%d-%H%M%S", gmtime())
        self.tb.set_base_name(self.file_base_name)
        self.metadata['t_start'] = time() 
        return 

    def start_clicked(self) :
        print("Enter start_clicked()")
        self.timer.start(self.dwell_time_ms) 
        self.RunLabel.setText("Running")
        self.RunLabel.setStyleSheet("color: green;")
        writeMetadata(self.metadata,self.file_base_name)
        print("In start_clicked(): metadata written")
        self.tb.start() 
        #self.tb.wait() 
        print("In start_clicked(): top_block running")
        return
    
    def stop_clicked(self) :
        self.timer.stop() 
        self.RunLabel.setText("Stopped")
        self.RunLabel.setStyleSheet("color: red;")
        #self.tb.blocks_head_0.set_length(0)
        self.tb.stop()
        self.tb.wait() 
        print("In stop_clicked(): top_block stopped")
        writeMetadata(self.metadata,self.file_base_name)
        print("In stop_clicked(): top_block metadata written")
        return
    
    def dwell_time_changed(self) :
        self.dwell_time = self.dwell_time_spinner.value() 
        self.dwell_time_ms = int(1000*self.dwell_time)
        self.timer.start(self.dwell_time_ms)
        #print("New dwell time={0:.3f}".format(self.dwell_time))
        return 

# begin execution here 
parser = ArgumentParser()
parser.add_argument("--device", type=str, default="/dev/ttyACM0", help="GPIO device")
parser.add_argument("--timeout", type=float, default=0.050, help="Read timeout")
parser.add_argument("--run_time",type=int,default=100000,help="run time in seconds")
parser.add_argument("--dwell_time",type=int,default=60,help="run time in seconds")
parser.add_argument("--fft_size",type=int,default=8192,help="fft_size")

args = parser.parse_args()

GPIO = NumatoGPIO.NumatoGPIO(args.device,timeout=args.timeout)
app = QApplication([])
window = MainWindow(args,GPIO)
window.show()
app.exec_()

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QCheckBox, QGridLayout, QPushButton, QLabel, QDoubleSpinBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import LED 
import NumatoGPIO 
import xmlrpc.client
from argparse import ArgumentParser 
from time import sleep 

class MainWindow(QMainWindow):
    def __init__(self,args,GPIO):
        super().__init__()
        self.setWindowTitle("MUX Controller")
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
            #self.CBs[i].stateChanged.connect(self.checkbox_changed)
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
        self.dwell_time_spinner.setValue(10.)
        self.dwell_time_ms = int(1000*self.dwell_time_spinner.value())
        self.dwell_time_spinner.valueChanged.connect(self.dwell_time_changed)
        layout.addWidget(self.dwell_time_spinner,4,2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_channel)
        
        if (args.xmlurl != None):
            self.proxy = xmlrpc.client.ServerProxy(args.xmlurl)
            print("Before proxy call")
            result = self.proxy.set_filename("Channel_00")
            print("After proxy call result={0}".format(result))
            
    def update_channel(self) :
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
        if (args.xmlurl != None): result = self.proxy.set_filename("/dev/null")
        sleep(1.)
        self.LEDs[self.channel].set_on(False)
        self.channel = new_chan 
        self.LEDs[self.channel].set_on(True)
        
        #update channel select hardware
        if self.GPIO_good : GPIO.write_all_outputs(self.channel)

        sleep(1.0)
        if (args.xmlurl != None): result = self.proxy.set_filename("Channel_{0:02d}".format(self.channel))
        return 


    def start_clicked(self) :
        self.timer.start(self.dwell_time_ms) 
        self.RunLabel.setText("Running")
        self.RunLabel.setStyleSheet("color: green;")
        return
    
    def stop_clicked(self) :
        self.timer.stop() 
        self.RunLabel.setText("Stopped")
        self.RunLabel.setStyleSheet("color: red;")
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
parser.add_argument("--xmlurl", type=str, default="http://localhost:14300", help="XMLPORT")
parser.add_argument("--timeout", type=float, default=0.050, help="Read timeout")
args = parser.parse_args()

GPIO = NumatoGPIO.NumatoGPIO(args.device,timeout=args.timeout)
app = QApplication([])
window = MainWindow(args,GPIO)
window.show()
app.exec_()

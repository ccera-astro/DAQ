# test file reader
import numpy as np
import time 


file_name = "test.dat"
fid = open(file_name,"wb")

data = np.linspace(0.,1.,2048,dtype=np.float32)
while True :
    data.tofile(fid, sep="")
    time.sleep(2.)

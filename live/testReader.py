# test file reader
import numpy as np
import time 

file_name = "test.dat"

nRecords, offset = 0, 0  
while True :
    nRecords += 1 
    data = np.fromfile(file_name,count=2048,offset=offset,dtype=np.float32)
    
    if len(data) < 2048 :
        print("No data ... sleeping.") 
        time.sleep(0.5) 
    else :
        print("nRecords={0:d} len(data)={1:d}".format(nRecords,len(data)))
        offset += 4*2048


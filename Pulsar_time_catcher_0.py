"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""
"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import time
import math
from gnuradio.fft import window
import os
import signal

class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Time Catcher"""

    def __init__(self, fftsize=32,tsfile="tsfile.txt"):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Time Catcher',   # will show up in GRC
            in_sig=[(np.float32,fftsize)],
            out_sig=None
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.fftsize = fftsize
        self.tsfile = tsfile
        self.first = True
        

    def work(self, input_items, output_items):
        """Capture timestamp on first record"""
        if (self.first == True):
            fp = open(self.tsfile, "w")
            fp.write("%13.6f\n" % time.time())
            fp.close()
            self.first = False
        return len(input_items[0])

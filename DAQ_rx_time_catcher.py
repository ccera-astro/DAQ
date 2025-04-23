"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt
import time 


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Catch the first rx_timestamp"""

    def __init__(self, rxfile="rxfile.txt",fftsize=32,crate=2500,srate=25e6):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='rx_time catcher',   # will show up in GRC
            in_sig=[np.complex64],
            out_sig=None
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.rxfile = rxfile
        self.first = True
        
        #
        # FFT outputs occur at srate/fftsize
        #
        self.fftrate = srate/fftsize
        
        #
        # This is then decimated at "self.decim" to produce the actual outputs
        #
        self.decim = self.fftrate / crate
        
        #
        # Which means the first output sample is produced at a time that is
        #  offset from the first input sample
        #
        self.offset = (1.0/self.fftrate) * self.decim

    def work(self, input_items, output_items):
        if (self.first == True):
            # Get rx_time tag
            self.first = False
            tags = self.get_tags_in_window(0, 0, len(input_items[0]))
            for tag in tags:
                key = pmt.to_python(tag.key) # convert from PMT to python string
                value = pmt.to_python(tag.value) # Note that the type(value) can be several things, it depends what PMT type it was
                if (key == "rx_time"):
                    break
            fp = open(self.rxfile, "w")
            #fp.write("%s" % str(value))
            timestump = float(value[0])+float(value[1])
            timestump += self.offset
            fp.write("%13.7f\n" % timestump)
            fp.write("{0:.7f}\n".format(time.time()))
            fp.close()
        return len(input_items[0])

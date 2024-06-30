#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: DAQ
# GNU Radio version: 3.10.7.0

from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
import DAQ_rx_time_catcher as rx_time_catcher  # embedded python block
import math




class DAQ(gr.top_block):

    def __init__(self, base_name='Doppler', decimation_factor=10000, device="type=n3xx,product=n310,addr=192.168.20.2", fft_size=2048, frequency=1420.4058e6, mclock=125e6, pps='gpsdo', refclock='gpsdo', rfgain=67.2, samp_rate=1.25e7, seconds=3600, subdev="A:0 A:1"):
        gr.top_block.__init__(self, "DAQ", catch_exceptions=True)

        ##################################################
        # Parameters
        ##################################################
        self.base_name = base_name
        self.decimation_factor = decimation_factor
        self.device = device
        self.fft_size = fft_size
        self.frequency = frequency
        self.mclock = mclock
        self.pps = pps
        self.refclock = refclock
        self.rfgain = rfgain
        self.samp_rate = samp_rate
        self.seconds = seconds
        self.subdev = subdev

        ##################################################
        # Variables
        ##################################################
        self.alpha_IIR = alpha_IIR = 2./decimation_factor

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join((device, "master_clock_rate=%f" % mclock)),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,2)),
            ),
        )
        self.uhd_usrp_source_0.set_clock_source(refclock, 0)
        self.uhd_usrp_source_0.set_time_source(pps, 0)
        self.uhd_usrp_source_0.set_subdev_spec(subdev, 0)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        # Set the time to GPS time on next PPS
        # get_mboard_sensor("gps_time") returns just after the PPS edge,
        # thus add one second and set the time on the next PPS
        self.uhd_usrp_source_0.set_time_next_pps(uhd.time_spec(self.uhd_usrp_source_0.get_mboard_sensor("gps_time").to_int() + 1.0))
        # Sleep 1 second to ensure next PPS has come
        time.sleep(1)

        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(frequency,((samp_rate/2.0)+100e3)), 0)
        self.uhd_usrp_source_0.set_antenna("RX2", 0)
        self.uhd_usrp_source_0.set_gain(rfgain, 0)

        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(frequency,((samp_rate/2.0)+100e3)), 1)
        self.uhd_usrp_source_0.set_antenna("RX2", 1)
        self.uhd_usrp_source_0.set_gain(rfgain, 1)
        self.single_pole_iir_filter_xx_0_0 = filter.single_pole_iir_filter_ff(alpha_IIR, fft_size)
        self.single_pole_iir_filter_xx_0 = filter.single_pole_iir_filter_ff(alpha_IIR, fft_size)
        self.rx_time_catcher = rx_time_catcher.blk(rxfile=base_name + "_ts.txt", fftsize=32, crate=samp_rate/fft_size/decimation_factor, srate=samp_rate)
        self.fft_vxx_0_0 = fft.fft_vcc(fft_size, True, window.blackmanharris(fft_size), True, 1)
        self.fft_vxx_0 = fft.fft_vcc(fft_size, True, window.blackmanharris(fft_size), True, 1)
        self.blocks_stream_to_vector_0_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_size)
        self.blocks_keep_one_in_n_2 = blocks.keep_one_in_n(gr.sizeof_gr_complex*1, 50)
        self.blocks_keep_one_in_n_0_0 = blocks.keep_one_in_n(gr.sizeof_float*fft_size, decimation_factor)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*fft_size, decimation_factor)
        self.blocks_head_0 = blocks.head(gr.sizeof_gr_complex*1, (int(seconds*samp_rate)))
        self.blocks_file_sink_1 = blocks.file_sink(gr.sizeof_float*fft_size, base_name +"_2.raw", False)
        self.blocks_file_sink_1.set_unbuffered(False)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*fft_size, base_name+"_1.raw", False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_complex_to_mag_squared_0_0 = blocks.complex_to_mag_squared(fft_size)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(fft_size)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.single_pole_iir_filter_xx_0, 0))
        self.connect((self.blocks_complex_to_mag_squared_0_0, 0), (self.single_pole_iir_filter_xx_0_0, 0))
        self.connect((self.blocks_head_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_keep_one_in_n_0_0, 0), (self.blocks_file_sink_1, 0))
        self.connect((self.blocks_keep_one_in_n_2, 0), (self.rx_time_catcher, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.blocks_stream_to_vector_0_0, 0), (self.fft_vxx_0_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.fft_vxx_0_0, 0), (self.blocks_complex_to_mag_squared_0_0, 0))
        self.connect((self.single_pole_iir_filter_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect((self.single_pole_iir_filter_xx_0_0, 0), (self.blocks_keep_one_in_n_0_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_head_0, 0))
        self.connect((self.uhd_usrp_source_0, 1), (self.blocks_keep_one_in_n_2, 0))
        self.connect((self.uhd_usrp_source_0, 1), (self.blocks_stream_to_vector_0_0, 0))


    def get_base_name(self):
        return self.base_name

    def set_base_name(self, base_name):
        self.base_name = base_name
        self.blocks_file_sink_0.open(self.base_name+"_1.raw")
        self.blocks_file_sink_1.open(self.base_name +"_2.raw")
        self.rx_time_catcher.rxfile = self.base_name + "_ts.txt"

    def get_decimation_factor(self):
        return self.decimation_factor

    def set_decimation_factor(self, decimation_factor):
        self.decimation_factor = decimation_factor
        self.set_alpha_IIR(2./self.decimation_factor)
        self.blocks_keep_one_in_n_0.set_n(self.decimation_factor)
        self.blocks_keep_one_in_n_0_0.set_n(self.decimation_factor)

    def get_device(self):
        return self.device

    def set_device(self, device):
        self.device = device

    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.frequency,((self.samp_rate/2.0)+100e3)), 0)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.frequency,((self.samp_rate/2.0)+100e3)), 1)

    def get_mclock(self):
        return self.mclock

    def set_mclock(self, mclock):
        self.mclock = mclock

    def get_pps(self):
        return self.pps

    def set_pps(self, pps):
        self.pps = pps

    def get_refclock(self):
        return self.refclock

    def set_refclock(self, refclock):
        self.refclock = refclock

    def get_rfgain(self):
        return self.rfgain

    def set_rfgain(self, rfgain):
        self.rfgain = rfgain
        self.uhd_usrp_source_0.set_gain(self.rfgain, 0)
        self.uhd_usrp_source_0.set_gain(self.rfgain, 1)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_head_0.set_length((int(self.seconds*self.samp_rate)))
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.frequency,((self.samp_rate/2.0)+100e3)), 0)
        self.uhd_usrp_source_0.set_center_freq(uhd.tune_request(self.frequency,((self.samp_rate/2.0)+100e3)), 1)

    def get_seconds(self):
        return self.seconds

    def set_seconds(self, seconds):
        self.seconds = seconds
        self.blocks_head_0.set_length((int(self.seconds*self.samp_rate)))

    def get_subdev(self):
        return self.subdev

    def set_subdev(self, subdev):
        self.subdev = subdev

    def get_alpha_IIR(self):
        return self.alpha_IIR

    def set_alpha_IIR(self, alpha_IIR):
        self.alpha_IIR = alpha_IIR
        self.single_pole_iir_filter_xx_0.set_taps(self.alpha_IIR)
        self.single_pole_iir_filter_xx_0_0.set_taps(self.alpha_IIR)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--base-name", dest="base_name", type=str, default='Doppler',
        help="Set Base File Name [default=%(default)r]")
    parser.add_argument(
        "--decimation-factor", dest="decimation_factor", type=intx, default=10000,
        help="Set Decimation Factor [default=%(default)r]")
    parser.add_argument(
        "--device", dest="device", type=str, default="type=n3xx,product=n310,addr=192.168.20.2",
        help="Set Device address string [default=%(default)r]")
    parser.add_argument(
        "--fft-size", dest="fft_size", type=intx, default=2048,
        help="Set fft_size [default=%(default)r]")
    parser.add_argument(
        "--frequency", dest="frequency", type=eng_float, default=eng_notation.num_to_str(float(1420.4058e6)),
        help="Set Center Frequency (Hz) [default=%(default)r]")
    parser.add_argument(
        "--mclock", dest="mclock", type=eng_float, default=eng_notation.num_to_str(float(125e6)),
        help="Set Master Clock Rate [default=%(default)r]")
    parser.add_argument(
        "--pps", dest="pps", type=str, default='gpsdo',
        help="Set PPS Clock SOurce [default=%(default)r]")
    parser.add_argument(
        "--refclock", dest="refclock", type=str, default='gpsdo',
        help="Set Reference clock type [default=%(default)r]")
    parser.add_argument(
        "--rfgain", dest="rfgain", type=eng_float, default=eng_notation.num_to_str(float(67.2)),
        help="Set RF Gain [default=%(default)r]")
    parser.add_argument(
        "--samp-rate", dest="samp_rate", type=eng_float, default=eng_notation.num_to_str(float(1.25e7)),
        help="Set Sample Rate [default=%(default)r]")
    parser.add_argument(
        "--seconds", dest="seconds", type=intx, default=3600,
        help="Set Seconds [default=%(default)r]")
    parser.add_argument(
        "--subdev", dest="subdev", type=str, default="A:0 A:1",
        help="Set Sub-device spec [default=%(default)r]")
    return parser


def main(top_block_cls=DAQ, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(base_name=options.base_name, decimation_factor=options.decimation_factor, device=options.device, fft_size=options.fft_size, frequency=options.frequency, mclock=options.mclock, pps=options.pps, refclock=options.refclock, rfgain=options.rfgain, samp_rate=options.samp_rate, seconds=options.seconds, subdev=options.subdev)

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    tb.wait()


if __name__ == '__main__':
    main()

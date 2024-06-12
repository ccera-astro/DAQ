#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Pulsar
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
import Pulsar_rx_time_catcher as rx_time_catcher  # embedded python block
import math




class Pulsar(gr.top_block):

    def __init__(self, base_name='Pulsar', decimation_factor=250, f1=1420.4058e6, f2=1420.4058e6, f3=1420.4058e6, f4=1420.4058e6, g1=75, g2=75, g3=75, g4=75, samp_rate=2.5e7, seconds=3600):
        gr.top_block.__init__(self, "Pulsar", catch_exceptions=True)

        ##################################################
        # Parameters
        ##################################################
        self.base_name = base_name
        self.decimation_factor = decimation_factor
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.g1 = g1
        self.g2 = g2
        self.g3 = g3
        self.g4 = g4
        self.samp_rate = samp_rate
        self.seconds = seconds

        ##################################################
        # Variables
        ##################################################
        self.fft_size = fft_size = 32
        self.alpha_IIR = alpha_IIR = 2./decimation_factor

        ##################################################
        # Blocks
        ##################################################

        self.uhd_usrp_source_0 = uhd.usrp_source(
            ",".join(('addr=192.168.40.2,type=x300', 'master_clock_rate=200e6', "master_clock_rate=200e6")),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,2)),
            ),
        )
        self.uhd_usrp_source_0.set_clock_source('external', 0)
        self.uhd_usrp_source_0.set_subdev_spec("A:0 A:1", 0)
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        _last_pps_time = self.uhd_usrp_source_0.get_time_last_pps().get_real_secs()
        # Poll get_time_last_pps() every 50 ms until a change is seen
        while(self.uhd_usrp_source_0.get_time_last_pps().get_real_secs() == _last_pps_time):
            time.sleep(0.05)
        # Set the time to PC time on next PPS
        self.uhd_usrp_source_0.set_time_next_pps(uhd.time_spec(int(time.time()) + 1.0))
        # Sleep 1 second to ensure next PPS has come
        time.sleep(1)

        self.uhd_usrp_source_0.set_center_freq(f1, 0)
        self.uhd_usrp_source_0.set_antenna('RX1', 0)
        self.uhd_usrp_source_0.set_gain(g1, 0)

        self.uhd_usrp_source_0.set_lo_source('internal', uhd.ALL_LOS, 0)
        self.uhd_usrp_source_0.set_lo_export_enabled(True, uhd.ALL_LOS, 0)
        self.uhd_usrp_source_0.set_center_freq(f2, 1)
        self.uhd_usrp_source_0.set_antenna('RX2', 1)
        self.uhd_usrp_source_0.set_gain(g2, 1)

        self.uhd_usrp_source_0.set_lo_source('companion', uhd.ALL_LOS, 1)
        self.uhd_usrp_source_0.set_lo_export_enabled(False, uhd.ALL_LOS, 1)
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

    def get_f1(self):
        return self.f1

    def set_f1(self, f1):
        self.f1 = f1
        self.uhd_usrp_source_0.set_center_freq(self.f1, 0)

    def get_f2(self):
        return self.f2

    def set_f2(self, f2):
        self.f2 = f2
        self.uhd_usrp_source_0.set_center_freq(self.f2, 1)

    def get_f3(self):
        return self.f3

    def set_f3(self, f3):
        self.f3 = f3
        self.uhd_usrp_source_0.set_center_freq(self.f3, 2)

    def get_f4(self):
        return self.f4

    def set_f4(self, f4):
        self.f4 = f4
        self.uhd_usrp_source_0.set_center_freq(self.f4, 3)

    def get_g1(self):
        return self.g1

    def set_g1(self, g1):
        self.g1 = g1
        self.uhd_usrp_source_0.set_gain(self.g1, 0)

    def get_g2(self):
        return self.g2

    def set_g2(self, g2):
        self.g2 = g2
        self.uhd_usrp_source_0.set_gain(self.g2, 1)

    def get_g3(self):
        return self.g3

    def set_g3(self, g3):
        self.g3 = g3
        self.uhd_usrp_source_0.set_gain(self.g3, 2)

    def get_g4(self):
        return self.g4

    def set_g4(self, g4):
        self.g4 = g4
        self.uhd_usrp_source_0.set_gain(self.g4, 3)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_head_0.set_length((int(self.seconds*self.samp_rate)))
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_seconds(self):
        return self.seconds

    def set_seconds(self, seconds):
        self.seconds = seconds
        self.blocks_head_0.set_length((int(self.seconds*self.samp_rate)))

    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size

    def get_alpha_IIR(self):
        return self.alpha_IIR

    def set_alpha_IIR(self, alpha_IIR):
        self.alpha_IIR = alpha_IIR
        self.single_pole_iir_filter_xx_0.set_taps(self.alpha_IIR)
        self.single_pole_iir_filter_xx_0_0.set_taps(self.alpha_IIR)



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--base-name", dest="base_name", type=str, default='Pulsar',
        help="Set Base File Name [default=%(default)r]")
    parser.add_argument(
        "--decimation-factor", dest="decimation_factor", type=intx, default=250,
        help="Set Decimation Factor [default=%(default)r]")
    parser.add_argument(
        "--f1", dest="f1", type=eng_float, default=eng_notation.num_to_str(float(1420.4058e6)),
        help="Set Chan 1 freq [default=%(default)r]")
    parser.add_argument(
        "--f2", dest="f2", type=eng_float, default=eng_notation.num_to_str(float(1420.4058e6)),
        help="Set Chan 2 freq [default=%(default)r]")
    parser.add_argument(
        "--f3", dest="f3", type=eng_float, default=eng_notation.num_to_str(float(1420.4058e6)),
        help="Set Chan 3 freq [default=%(default)r]")
    parser.add_argument(
        "--f4", dest="f4", type=eng_float, default=eng_notation.num_to_str(float(1420.4058e6)),
        help="Set Chan 4 freq [default=%(default)r]")
    parser.add_argument(
        "--g1", dest="g1", type=eng_float, default=eng_notation.num_to_str(float(75)),
        help="Set Chan 1 gain [default=%(default)r]")
    parser.add_argument(
        "--g2", dest="g2", type=eng_float, default=eng_notation.num_to_str(float(75)),
        help="Set Chan 2 gain [default=%(default)r]")
    parser.add_argument(
        "--g3", dest="g3", type=eng_float, default=eng_notation.num_to_str(float(75)),
        help="Set Chan 3 gain [default=%(default)r]")
    parser.add_argument(
        "--g4", dest="g4", type=eng_float, default=eng_notation.num_to_str(float(75)),
        help="Set Chan 4 gain [default=%(default)r]")
    parser.add_argument(
        "--samp-rate", dest="samp_rate", type=eng_float, default=eng_notation.num_to_str(float(2.5e7)),
        help="Set Sample Rate [default=%(default)r]")
    parser.add_argument(
        "--seconds", dest="seconds", type=intx, default=3600,
        help="Set Seconds [default=%(default)r]")
    return parser


def main(top_block_cls=Pulsar, options=None):
    if options is None:
        options = argument_parser().parse_args()
    tb = top_block_cls(base_name=options.base_name, decimation_factor=options.decimation_factor, f1=options.f1, f2=options.f2, f3=options.f3, f4=options.f4, g1=options.g1, g2=options.g2, g3=options.g3, g4=options.g4, samp_rate=options.samp_rate, seconds=options.seconds)

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

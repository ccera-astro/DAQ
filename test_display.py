#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Test Display
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import math
import sip



class test_display(gr.top_block, Qt.QWidget):

    def __init__(self, f1=1410e6, f2=1410e6, f3=611e6, f4=1000e6, fft_size=2048, srate=10e6):
        gr.top_block.__init__(self, "Test Display", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Test Display")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "test_display")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Parameters
        ##################################################
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.fft_size = fft_size
        self.srate = srate

        ##################################################
        # Variables
        ##################################################
        self.winpower = winpower = sum([x*x for x in window.blackman_harris(fft_size)])
        self.samp_rate = samp_rate = srate
        self.log10_k = log10_k = -20*math.log10(fft_size)-10*math.log10(winpower/fft_size)

        ##################################################
        # Blocks
        ##################################################

        self.zeromq_sub_source_0 = zeromq.sub_source(gr.sizeof_float, fft_size, 'tcp://127.0.0.1:14200', 100, False, (-1), '', False)
        self.qtgui_vector_sink_f_0 = qtgui.vector_sink_f(
            fft_size,
            (-(samp_rate/2)),
            (samp_rate/fft_size),
            "Frequency Offset",
            "dB",
            "Spectrum",
            2, # Number of inputs
            None # parent
        )
        self.qtgui_vector_sink_f_0.set_update_time(0.10)
        self.qtgui_vector_sink_f_0.set_y_axis((-100), 10)
        self.qtgui_vector_sink_f_0.enable_autoscale(False)
        self.qtgui_vector_sink_f_0.enable_grid(True)
        self.qtgui_vector_sink_f_0.set_x_axis_units("")
        self.qtgui_vector_sink_f_0.set_y_axis_units("")
        self.qtgui_vector_sink_f_0.set_ref_level(0)


        labels = ["%.3fMHz" % (f1 / 1.0e6), "%.3fMHz" % (f2 / 1.0e6), "%.3fMHz" % (f3 / 1.0e6), "%.3fMHz" % (f4 / 1.0e6), '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(2):
            if len(labels[i]) == 0:
                self.qtgui_vector_sink_f_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_vector_sink_f_0.set_line_label(i, labels[i])
            self.qtgui_vector_sink_f_0.set_line_width(i, widths[i])
            self.qtgui_vector_sink_f_0.set_line_color(i, colors[i])
            self.qtgui_vector_sink_f_0.set_line_alpha(i, alphas[i])

        self._qtgui_vector_sink_f_0_win = sip.wrapinstance(self.qtgui_vector_sink_f_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_vector_sink_f_0_win)
        self.blocks_nlog10_ff_0_0 = blocks.nlog10_ff(10, fft_size, log10_k)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10, fft_size, log10_k)
        self.blocks_deinterleave_0 = blocks.deinterleave(gr.sizeof_float*fft_size, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_deinterleave_0, 0), (self.blocks_nlog10_ff_0, 0))
        self.connect((self.blocks_deinterleave_0, 1), (self.blocks_nlog10_ff_0_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.qtgui_vector_sink_f_0, 0))
        self.connect((self.blocks_nlog10_ff_0_0, 0), (self.qtgui_vector_sink_f_0, 1))
        self.connect((self.zeromq_sub_source_0, 0), (self.blocks_deinterleave_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "test_display")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_f1(self):
        return self.f1

    def set_f1(self, f1):
        self.f1 = f1

    def get_f2(self):
        return self.f2

    def set_f2(self, f2):
        self.f2 = f2

    def get_f3(self):
        return self.f3

    def set_f3(self, f3):
        self.f3 = f3

    def get_f4(self):
        return self.f4

    def set_f4(self, f4):
        self.f4 = f4

    def get_fft_size(self):
        return self.fft_size

    def set_fft_size(self, fft_size):
        self.fft_size = fft_size
        self.set_log10_k(-20*math.log10(self.fft_size)-10*math.log10(self.winpower/self.fft_size))
        self.set_winpower(sum([x*x for x in window.blackman_harris(self.fft_size)]))
        self.qtgui_vector_sink_f_0.set_x_axis((-(self.samp_rate/2)), (self.samp_rate/self.fft_size))

    def get_srate(self):
        return self.srate

    def set_srate(self, srate):
        self.srate = srate
        self.set_samp_rate(self.srate)

    def get_winpower(self):
        return self.winpower

    def set_winpower(self, winpower):
        self.winpower = winpower
        self.set_log10_k(-20*math.log10(self.fft_size)-10*math.log10(self.winpower/self.fft_size))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_vector_sink_f_0.set_x_axis((-(self.samp_rate/2)), (self.samp_rate/self.fft_size))

    def get_log10_k(self):
        return self.log10_k

    def set_log10_k(self, log10_k):
        self.log10_k = log10_k



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "--f1", dest="f1", type=eng_float, default=eng_notation.num_to_str(float(1410e6)),
        help="Set Channel 1 Freq [default=%(default)r]")
    parser.add_argument(
        "--f2", dest="f2", type=eng_float, default=eng_notation.num_to_str(float(1410e6)),
        help="Set Channel 2 Freq [default=%(default)r]")
    parser.add_argument(
        "--f3", dest="f3", type=eng_float, default=eng_notation.num_to_str(float(611e6)),
        help="Set Channel 3 Freq [default=%(default)r]")
    parser.add_argument(
        "--f4", dest="f4", type=eng_float, default=eng_notation.num_to_str(float(1000e6)),
        help="Set Channel 4 Freq [default=%(default)r]")
    parser.add_argument(
        "--fft-size", dest="fft_size", type=intx, default=2048,
        help="Set FFT Size [default=%(default)r]")
    parser.add_argument(
        "--srate", dest="srate", type=eng_float, default=eng_notation.num_to_str(float(10e6)),
        help="Set Sample Rate [default=%(default)r]")
    return parser


def main(top_block_cls=test_display, options=None):
    if options is None:
        options = argument_parser().parse_args()

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(f1=options.f1, f2=options.f2, f3=options.f3, f4=options.f4, fft_size=options.fft_size, srate=options.srate)

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()

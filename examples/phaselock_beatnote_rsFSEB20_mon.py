# A class to pull together the FSEB20 spectrum analyzer code and monitor the
# phaselock beatnote frequency and width.
# And publish those values.
#
#
# Notes for phase lock:
# Zooming in on the center feature for getting the 3dB width:
#  sa.set_rbw('100Hz') and sa.set_freq_span('1kHz') go together nicely
#  sa.set_rbw('30Hz') and sa.set_freq_span('250Hz') go together nicely
# on 10Hz rbw and 250Hz span you can see a double peak if the freq shifts
# around during the scan. A span of 50Hz shows a bumpy mass for the feature.
#
# 5kHz rbw and 2MHz span is a quick sweep speed for looking for the peak.
# Ratio is about 1/1000
#
# Remember that the 3dB width of the peak will be limited by the rbw.
# If rbw is too big, the values returned will be about equal to rbw.

import numpy as np
import time
import os

parent_dir = "/home/labuser/googledrive/code/Samarium_control/"

os.chdir(parent_dir + "Widgets/Objects")
import RohdeSchwarz_FSEB20_spectrum_ana as SA
os.chdir(parent_dir + "Widgets/python_gui_v2")
import zmqPublisher
from GUIClasses import StreamGrabber



class PhaselockMonitorFSEB20():

    def __init__(self):

        # Create spectrum ana object and connect
        self.sa = SA.SpectrumAnaFSEB20("/dev/RohdeSchwarz_SpecAna", 20)

        self.pub_port = 5572
        self.publisher = zmqPublisher.zmqPublisher(self.pub_port, 'phaselock_beatnote_rsFSEB20')
        self.pub_interval = 0.4# (s) interval between publishes
        self.pub_last_time = 0.0# time.time() # 0.0 means it will publish immediately

        self.bnGrabber = StreamGrabber(port=5546,topic="beatnote_freq",ip_addr='localhost')

        self.sleep_time = 0.1# (s) time to sleep between message checks

        # Details
        self.zoomed_freq_span = 250.0# Hz
        self.zoomed_rbw = 20.0# Hz
        self.bn_compare_tol = 0.05# MHz, tolerance before freq counter bn has 'changed'


    def get_beatnote_counter_freq(self):
        subscrb_msg = self.bnGrabber.read_on_demand()
        #print(subscrb_msg)
        bn = subscrb_msg.decode().split()[2]# string
        #print(bn)
        return bn

    def coarse_center_on_beatnote(self):
        # grab beatnote freq from freq counter
        bn = self.get_beatnote_counter_freq()
        # center freq on beatnote
        self.sa.set_center_freq(bn+'MHz')# send with MHz suffix
        # set freq span and sensibly for fast sweep rate
        self.sa.set_freq_span('5MHz')
        self.sa.set_rbw('10kHz')
        # wait for one sweep time
        st = self.sa.get_sweep_time()
        #print(st)
        time.sleep(float(st))
        # leave zooming in for another function

    def get_peak_freq(self):
        # assumes that the beatnote is on the screen
        # assumes that a full sweep has happened
        self.sa.set_marker_onoff('ON')
        self.sa.set_marker_to_trace('1')
        self.sa.set_marker_at_max()
        return self.sa.get_marker_freq()

    def get_3db_width(self):
        # assumes that the beatnote is on the screen
        # assumes that a full sweep has happened
        self.sa.set_marker_onoff('ON')
        self.sa.set_marker_to_trace('1')
        self.sa.set_marker_at_max()
        self.sa.set_marker_ndbdown_val('3dB')
        self.sa.set_marker_ndbdown_onoff('ON')
        return self.sa.get_marker_ndbdown_fspacing()

    def get_3db_freqs(self):
        # assumes that the beatnote is on the screen
        # assumes that a full sweep has happened
        self.sa.set_marker_onoff('ON')
        self.sa.set_marker_to_trace('1')
        self.sa.set_marker_at_max()
        self.sa.set_marker_ndbdown_val('3dB')
        self.sa.set_marker_ndbdown_onoff('ON')
        return self.sa.get_marker_ndbdown_freqs()


    def wait_for_sweep(self):
        """
        Gets how long a sweep is and then waits just a bit longer.
        """
        t = float(self.sa.get_sweep_time())
        time.sleep(t*1.01)

    def do_sweep_cont(self):
        """
        Initiates a sweep and then waits for it to happen.

        Note that this is not a single sweep and it keeps sweeping afterwards.
        """
        self.sa.initiate_meas()
        self.wait_for_sweep()

    def narrow_on_beatnote(self):
        """
        Zooms in to a characteristic range for measuring the beatnote width.
        """
        # assumes that the beatnote is on the screen

        # Set rbw according to ratio of freq span
        ratio = 1.0/50.0
        freq_span = self.zoomed_freq_span
        rbw = self.zoomed_rbw
        self.sa.set_rbw_freq_span_ratio(str(ratio))
        self.sa.set_rbw_ratio_onoff('ON')

        self.wait_for_sweep()

        # First ensure we are centered
        peak_freq = self.get_peak_freq()
        print(peak_freq)
        self.sa.set_center_freq(peak_freq)

        # Get the current span and start ramping to the target span
        fs = float(self.sa.get_freq_span())
        spans = np.logspace(np.log10(fs), np.log10(freq_span), int(np.log10(fs)-np.log10(freq_span)))
        for sp in spans:
            print(sp)
            time.sleep(2)
            # set span
            self.sa.set_freq_span(str(sp))
            # wait for sweep
            self.wait_for_sweep()
            # update center to peak
            peak_freq = self.get_peak_freq()
            self.sa.set_center_freq(peak_freq)

        # finish at final settings
        self.sa.set_rbw(str(rbw))
        self.sa.set_freq_span(str(freq_span))



    def broaden_on_beatnote(self, freq_span = '5MHz'):
        """
        Zooms out to see the entire beatnote with side peaks.
        """
        self.sa.set_freq_span(freq_span)

    def check_beatnote_counter_fsweep(self):
        """
        Checks if the beatnote from the counter is within the freq spanned.

        Note that this is useless if the span is smaller than the resolution of
        the freq counter.
        """
        sp = float(self.sa.get_freq_span())
        print(sp)
        cf = float(self.sa.get_center_freq())
        print(cf)
        bn = float(self.get_beatnote_counter_freq())*1000*1000# MHz to Hz
        print(bn)
        if bn <= cf-0.5*sp or bn >= cf+0.5*sp:# if outside (conservative) range
            print("Freq counter value not in freq span.")
            return False
        return True

    def check_zoomed_in(self):
        """
        Checks if the spectrum analyzer settings are 'zoomed in'.
        """
        sp = float(self.sa.get_freq_span())
        if np.abs(sp - self.zoomed_freq_span) > 0.001:# compare to 1 mHz tol
            return False
        rbv = float(self.sa.get_rbw())
        if np.abs(rbv - self.zoomed_rbw) > 0.001:
            return False
        return True

    def start_loop(self, restart = True):

        if restart:
            self.coarse_center_on_beatnote()
            self.narrow_on_beatnote()

        last_bn_counter_freq = float(self.get_beatnote_counter_freq())

        while True:

            time.sleep(self.sleep_time)# not loop too fast

            # Check to make sure the phaselock is not being ramped
            # Could also do this check by an input socket to this class but
            # this is the way that only needs the beatnote counter publisher.
            bn_counter_freq = float(self.get_beatnote_counter_freq())
            if np.abs(last_bn_counter_freq - bn_counter_freq) > self.bn_compare_tol:
                # then phaselock is ramping and makes no sense to measure freq width
                print("Skipping loop because phaselock seems to be ramping")
                continue

            # Check we are still near the frequency counter
            cf = float(self.sa.get_center_freq())/1000/1000# Hz to MHz
            if np.abs(cf - bn_counter_freq) > self.bn_compare_tol:
                print("Centering on freq counter beatnote value")
                self.coarse_center_on_beatnote()
                continue# skip the rest and wait for another full scan

            # Check that we are zoomed in at correct settings
            if not self.check_zoomed_in():
                print("Zooming in")
                self.narrow_on_beatnote()
                continue

            # Now we should be centered on the feature and zoomed in
            # Do a sweep
            self.do_sweep_cont()

            # Get the peak freq and width
            pf = self.get_peak_freq()
            fw = self.get_3db_width()# FWHM in power

            # Also get details to publish too
            rbw = float(self.sa.get_rbw())

            # Center the sweep on the peak value for next time (might jitter)
            self.sa.set_center_freq(str(pf))

            # Publish if enough time has passed
            if time.time() > self.pub_last_time + self.pub_interval:
                data = (rbw, pf, fw)
                print(f"pub: {data}")
                self.publisher.publish_data(data)
                self.pub_last_time = time.time()





    def __del__(self):
        self.sa.close_connenction()
        self.publisher.close()
        self.bnGrabber.close()




if __name__ == '__main__':
    plm = PhaselockMonitorFSEB20()

    print("Start the monitor and publish loop with 'plm.start_loop()'")
    # plm.start_loop()

# Code to communicate with the RS FSEB20 Spectrum Analyzer.
# Connection is via Prologix GPIB-to-usb adapter. This requires some extra setup.
#
# Note: The code does not yet account for the fact that any CR, LF, ESC, and '+'
# characters will be intercepted by the Prologix adapter on their way to the
# GPIB device. They must be escaped. But since I'm not sending commands with
# those in them here, I will put that off until a later time.
# Really, there should be a short Prologix adapter class that this class has an
# instance of that has convenience functions for the Prologix's commands
# such as '++eos'. And that escapes those 4 characters before writing with
# pyvisa commands.
#
# Not all of the convenience functions have been tested.
#
#
# The RS SA terminates it's responses with '\n' ie 'LF'.


import numpy as np
import time

import pyvisa


class SpectrumAnaFSEB20():

    def __init__(self,
                    addr = "/dev/RohdeSchwarz_SpecAna",# the bare '/dev/ttyUSB4' also works
                    gpib_addr = 20):

        self.addr = addr# Set the "Serial" ie. USB connection address of the Prologix

        self.gpib_addr = gpib_addr# integer gpib address of device (default for this one is 20)

        self.rm = pyvisa.ResourceManager()

        self.open_connection()

        self.test_connection()

    # connect to the device
    def open_connection(self):
        """
        Make the connection to the device.
        """
        self.addr_string = f"ASRL{self.addr}::INSTR"
        print(f"Opening connection to {self.addr_string}")
        self.instr = self.rm.open_resource(self.addr_string)

        # Do any config of the Prologix here too
        self.instr.write(f"++addr {self.gpib_addr}")
        # !! other commands necesary here like ++eos, ++eoi, etc

        print("Connection opened.")

    def close_connection(self):
        """
        Close the connection to the device.
        """
        self.instr.close()

    # basic routines for writing commands and reading responses
    def write(self, command):
        """
        Write a command to the device.
        """
        self.instr.write(command)

    def read(self):
        """
        Read from the device.
        """
        s = self.instr.read()
        return s

    def query(self, command):
        """
        Shorthand for pyvisa's query function.
        """
        return self.instr.query(command).strip()


    # Generic convenience functions
    def test_connection(self):
        s = self.get_name()
        #print(type(s))
        print(s)
        if 'Rohde&Schwarz,FSEB 20' not in s:
            print("Testing connection failed. Wrong device or connection failed.")
            #raise("ERROR")
        return s

    def get_name(self):
        return self.query("*IDN?")

    def get_error(self):
        return self.query("SYSTEM:ERROR?")

    # Device specific functions
    # The table of contents for the command listing is on pdf page 498 (6.1)
    # I've written the manual's pages for each set of commands as a comment.

    # RBW functions
    # Sens:Band starts 6.167 (pdf page 668)

    def set_rbw(self, num_value):
        """
        Sets the analyzer's resoultion bandwidth.

        Values are rounded in 1|2|3|5 steps by the analyzer.
        """
        self.write(f"SENSe:BANDwidth:RESolution {num_value}")

    def get_rbw(self):
        """
        Gets the analyzer's resoultion bandwidth (Hz).
        """
        return self.query("SENSe:BANDwidth:RESolution?")

    def set_rbw_ratio_onoff(self, bool_value):
        """
        Sets whether the RBW is a ratio of freq span (ON) or not (OFF).
        """
        self.write(f"SENSe:BANDwidth:RESolution:AUTO {bool_value}")

    def set_rbw_freq_span_ratio(self, num_value):
        """
        Sets the ratio of (resolution bandwidth)/(frequency span).
        """
        self.write(f"SENSe:BANDwidth:RESolution:RATio {num_value}")

    # Frequency span functions
    # Sens:Freq subsection starts at 6.193 (pdf page 694)

    def set_freq_span(self, num_value):
        """
        Sets the analyzer's frequency span.
        """
        self.write(f"SENSe:FREQuency:SPAN {num_value}")

    def get_freq_span(self):
        """
        Gets the analyzer's frequency span (Hz).
        """
        return self.query("SENSe:FREQuency:SPAN?")

    def set_center_freq(self, num_value):
        """
        Sets the center frequency.
        """
        self.write(f":SENSe:FREQuency:CENTer {num_value}")

    def get_center_freq(self):
        """
        Gets the center frequency (Hz).
        """
        return self.query(":SENSe:FREQuency:CENTer?")

    # Sweep functions
    # Sens:swe starts 6.207 (pdf page 708)

    def get_sweep_time(self):
        """
        Gets the sweep time (s).
        """
        return self.query(":SENSe:SWEep:TIME?")

    # Ref level functions
    # Input subsystem starts 6.127 (pdf page 628)
    # Display subsystem starts 6.91 (pdf page 592)

    def set_ref_level(self, num_value, trace = '1', window = '1'):
        """
        Sets the ref level for a given trace (and window).

        Ex: '-10dBm'
        """
        self.write(f":DISPlay:WINDow{window}:TRACe{trace}:Y:SCALe:RLEVel {num_value}")

    def get_ref_level(self, trace = '1', window = '1'):
        """
        Gets the ref level for a given trace (and window).
        """
        return self.query(f":DISPlay:WINDow{window}:TRACe{trace}:Y:SCALe:RLEVel?")

    def set_rf_atten(self, num_value):
        """
        Sets the rf attenuation level.
        """
        self.write(f":INPut:ATTenuation {num_value}")

    def get_rf_atten(self):
        """
        Gets the rf attenuation level.
        """
        return self.query(":INPut:ATTenuation?")

    def set_y_range(self, num_value, trace = '1', window = '1'):
        """
        Sets the y scale per div for a given trace (and window).

        Ex: '100dB'
        """
        self.write(f":DISPlay:WINDow{window}:TRACe{trace}:Y:SCALe {num_value}")

    def get_y_range(self, trace = '1', window = '1'):
        """
        Gets the y scale per div for a given trace (and window).
        """
        return self.query(f":DISPlay:WINDow{window}:TRACe{trace}:Y:SCALe?")

    # Marker functions
    # Mark subsystem starts 6.36 (pdf page 537)
    # The marker functions here cover about 6.36 to 6.47
    # There is also a shape factor I didn't include here that uses T1 thru T4.

    def set_marker_onoff(self, bool_value, marker = '1', screen = '1'):
        """
        Sets marker<1to4> ON or OFF (on a given screen).
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:STATe {bool_value}")

    def set_marker_to_trace(self, num_value, marker = '1', screen = '1'):
        """
        Sets marker<1to4> to the given trace (on a given screen).
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:TRACe {num_value}")

    def set_marker_freq(self, num_value, marker = '1', screen = '1'):
        """
        Sets marker<1to4> to the given frequency (on a given screen).
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:X {num_value}")

    def get_marker_freq(self, marker = '1', screen = '1'):
        """
        Gets marker<1to4>'s frequency (on a given screen).
        """
        return self.query(f":CALCulate{screen}:MARKer{marker}:X?")

    def get_marker_value(self, marker = '1', screen = '1'):
        """
        Gets marker<1to4>'s value in the current units (on a given screen).
        """
        return self.query(f":CALCulate{screen}:MARKer{marker}:Y?")

    def set_marker_at_max(self, marker = '1', screen = '1'):
        """
        Sets marker<1to4> to the maximum value in the trace memory (on a given screen).
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:MAXimum:PEAK")

    def set_marker_ndbdown_val(self, num_value, marker = '1', screen = '1'):
        """
        Relative to marker<1to4>, creates temporary markers T1 and T2 that are
        positioned by n dB below the active reference marker.

        Ex: '3dB' for half power points.
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:FUNCtion:NDBDown {num_value}")

    def set_marker_ndbdown_onoff(self, bool_value, marker = '1', screen = '1'):
        """
        Switches the "N dB Down" function ON or OFF.
        """
        self.write(f":CALCulate{screen}:MARKer{marker}:FUNCtion:NDBDown:STATe {bool_value}")

    def get_marker_ndbdown_fspacing(self, marker = '1', screen = '1'):
        """
        Gets the value of the frequency spacing between T1 and T2 of the "N dB Down" function.
        """
        return self.query(f":CALCulate{screen}:MARKer{marker}:FUNCtion:NDBDown:RESult?")

    def get_marker_ndbdown_freqs(self, marker = '1', screen = '1'):
        """
        Gets the frequency values of T1 and T2 of the "N dB Down" function.

        The two frequency values are separated by a comma and in ascending order.
        """
        return self.query(f":CALCulate{screen}:MARKer{marker}:FUNCtion:NDBDown:FREQuency?")

    # Initiate functions
    # Init subsystem starts 6.125 (pdf page 626)

    def initiate_meas(self, screen = '1'):
        """
        Starts a new sweep or starts a single sweep (on a given screen).
        """
        self.write(f":INITiate{screen}:IMMediate")

    def set_freerun_onoff(self, bool_value, screen = '1'):
        """
        Sets trigger mode to free run (ON) or single sweep (OFF) (on a given screen).
        """
        self.write(f":INITiate{screen}:CONTinuous {bool_value}")

    def get_freerun_onoff(self, screen = '1'):
        """
        Gets the trigger mode of free run (ON) or single sweep (OFF) (on a given screen).
        """
        return self.query(f":INITiate{screen}:CONTinuous?")




if __name__ == '__main__':
    sa = SpectrumAnaFSEB20()


    # Composition function ideas (assume a marker is already active)
    # But these should go in whatever class is making use of this one.
    #
    # Find freq of max peak
    #sa.set_marker_at_max()
    #sa.get_marker_freq()
    #
    # Get the 3dB width. Might need to adjust rbw etc to get a good signal.
    #sa.set_marker_at_max()
    #sa.set_marker_ndbdown_val('3dB')
    #sa.set_marker_ndbdown_onoff('ON')
    #sa.get_marker_ndbdown_fspacing() or sa.get_marker_ndbdown_freqs()
    #
    # Center the peak on the screen
    #sa.set_marker_at_max()
    #freq = sa.get_marker_freq()
    #sa.set_center_freq(freq)
    #

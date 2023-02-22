# RohdeSchwarz_SpectAna
Interfacing with the Rohde-Schwarz spectrum analyzer FSEB20.

The primary file: “RohdeSchwarz_FSEB20_spectrum_ana.py”, wraps the hardware interface in a class. The second file is an example: “phaselock_beatnote_rsFSEB20_mon.py”, that uses the hardware interface (and the existing beatnote streaming code) for the task of centering the FSEB20 display on the phase lock beatnote. Further, it will automatically zoom in on the beatnote when it is stable and publish its own value for the beatnote along with the width of the beatnote.

## The FSEB20
A short summary of specs from the manual: The resolution bandwidth can be from 10 Hz to 10 MHz in 1, 2, 3, 5 steps. Video bandwidth from 1 Hz to 10 MHz in same step pattern. The frequency range is 9 kHz to 7 GHz. Due to the massive size of the manual, in the code that I wrote, I cite individual page numbers for easy reference later.

## Prologix GPIB to USB adapter
There is no usb or ethernet connection on the back of this spectrum analyzer. It does have a GPIB connection. So I used one of our Prologix GPIB to USB adapters to talk to it. I wrote a rules file on the Sm laptop computer that creates ‘/dev/RohdeSchwarz_SpecAna’ as an address. Note that this rule is actually for the serial number of this particular Prologix adapter and not the spectrum analyzer itself.

## Code notes
Note that the hardware python code does not yet account for the fact that any CR, LF, ESC, and ‘+’ characters will be intercepted by the Prologix adapter on their way to the GPIB device. They must be escaped. But since none of the commands that I’ve written convenience functions for use those characters I put that off until a later time. The only place where this is an issue is sending binary data to a device. Reading binary data is passed through the Prologix without issue. Ideally, there should be a short Prologix adapter class that has convenience functions for the Prologix’s own commands such as ‘++eos’. Such a class would also escape those four characters before writing to the device with pyvisa commands.

The beatnote measuring python code (example) uses the frequency counter to know roughly what is the beatnote frequency. If you run the function start_loop() then the code will attempt to zoom in on the beatnote and measure its FWHM automatically. It then publishes the results. It measures the width using the marker system of the spectrum analyzer. See the code for details.

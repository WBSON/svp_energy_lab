"""
Copyright (c) 2017, Sandia National Labs and SunSpec Alliance
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

Neither the names of the Sandia National Labs and SunSpec Alliance nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Questions can be directed to support@sunspec.org
"""

import time
import os
import traceback
import glob
import waveform
import dataset

try:
    import typhoon.api.hil_control_panel as cp
    from typhoon.api.schematic_editor import model
    import typhoon.api.pv_generator as pv
except Exception, e:
    print('Typhoon HIL API not installed. %s' % e)

data_points = [
    'TIME',
    'DC_V',
    'DC_I',
    'AC_VRMS',
    'AC_IRMS',
    'DC_P',
    'AC_S',
    'AC_P',
    'AC_Q',
    'AC_FREQ',
    'AC_PF',
    'TRIG',
    'TRIG_GRID'
]

# To be implemented later
# typhoon_points_asgc_1 = [
#     'time',
#     'V( V_DC3 )', # DC voltage
#     'I( Ipv )',
#     'V( Vrms1 )',
#     'I( Irms1 )',
#     'DC_P',  # calculated
#     'S',
#     'Pdc',
#     'Qdc',
#     'AC_FREQ',
#     'k',
#     'TRIG',
#     'TRIG_GRID'
# ]
#
# typhoon_points_asgc_3 = [
#     'time',
#     'V( V_DC3 )',  # DC voltage
#     'I( Ipv )',
#     'V( Vrms1 )',
#     'V( Vrms2 )',
#     'V( Vrms3 )',
#     'I( Irms1 )',
#     'I( Irms2 )',
#     'I( Irms3 )',
#     'DC_P',  # calculated
#     'S',
#     'Pdc',
#     'Qdc',
#     'AC_FREQ',
#     'k',
#     'TRIG',
#     'TRIG_GRID'
# ]
#
# typhoon_points_map = {
#     'ASGC3': typhoon_points_asgc_3,  # AGF circuit, 3 phase
#     'ASGC1': typhoon_points_asgc_1,  # AGF circuit, single phase
#     'ASGC_Fault': typhoon_points_asgc_fault,  # ride-through circuit
#     'ASGC_UI': typhoon_points_ui   # unintentional islanding circuit
# }

wfm_channels = ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']

wfm_typhoon_channel_type = {'V( Vrms1 )': 'analog',
                            'V( Vrms2 )': 'analog',
                            'V( Vrms3 )': 'analog',
                            'I( Irms1 )': 'analog',
                            'I( Irms2 )': 'analog',
                            'I( Irms3 )': 'analog',
                            'V( V_L1 )': 'analog',
                            'V( V_L2 )': 'analog',
                            'V( V_L3 )': 'analog',
                            'I( Ig1 )': 'analog',
                            'I( Ig2 )': 'analog',
                            'I( Ig3 )': 'analog',
                            'I( Ia )': 'analog',
                            'I( Ib )': 'analog',
                            'I( Ic )': 'analog',
                            'Trigger': 'digital',
                            'S1_fb': 'digital'}

wfm_typhoon_channels = {'AC_VRMS_1': 'V( Vrms1 )',
                        'AC_VRMS_2': 'V( Vrms2 )',
                        'AC_VRMS_3': 'V( Vrms3 )',
                        'AC_IRMS_1': 'I( Irms1 )',
                        'AC_IRMS_2': 'I( Irms2 )',
                        'AC_IRMS_3': 'I( Irms3 )',
                        'AC_V_1': 'V( V_L1 )',
                        'AC_V_2': 'V( V_L2 )',
                        'AC_V_3': 'V( V_L3 )',
                        'AC_I_1': 'I( Ia )',
                        'AC_I_2': 'I( Ib )',
                        'AC_I_3': 'I( Ic )',
                        # 'AC_I_1': 'I( Ig1 )',
                        # 'AC_I_2': 'I( Ig2 )',
                        # 'AC_I_3': 'I( Ig3 )',
                        'EXT': 'S1_fb',
                        'V( Vrms1 )': 'AC_VRMS_1',
                        'V( Vrms2 )': 'AC_VRMS_2',
                        'V( Vrms3 )': 'AC_VRMS_3',
                        'I( Irms1 )': 'AC_IRMS_1',
                        'I( Irms2 )': 'AC_IRMS_2',
                        'I( Irms3 )': 'AC_IRMS_3',
                        'V( V_L1 )': 'AC_V_1',
                        'V( V_L2 )': 'AC_V_2',
                        'V( V_L3 )': 'AC_V_3',
                        'I( Ia )': 'AC_I_1',
                        'I( Ib )': 'AC_I_2',
                        'I( Ic )': 'AC_I_3',
                        # 'I( Ig1 )': 'AC_I_1',
                        # 'I( Ig2 )': 'AC_I_2',
                        # 'I( Ig3 )': 'AC_I_3',
                        'S1_fb': 'EXT'}

event_map = {'Rising_Edge': 'Rising edge', 'Falling_Edge': 'Falling edge'}

class Device(object):

    def __init__(self, params=None):
        self.params = params
        self.data_points = list(data_points)
        self.points = None
        self.point_indexes = []

        self.ts = self.params.get('ts')

        # waveform settings
        self.wfm_sample_rate = None
        self.wfm_pre_trigger = None
        self.wfm_post_trigger = None
        self.wfm_trigger_level = None
        self.wfm_trigger_cond = None
        self.wfm_trigger_channel = None
        self.wfm_timeout = None
        self.wfm_channels = None
        self.wfm_capture_name = None
        # self.wfm_capture_name_path = r'C:\captured_signals\capture_test.mat'

        self.numberOfSamples = None
        self.triggerOffset = None
        self.decimation = 1
        self.captureSettings = None
        self.triggerSettings = None
        self.channelSettings = None

        # regular python list is used for data buffer
        self.capturedDataBuffer = []
        self.time_vector = None
        self.wfm_data = None
        self.signalsNames = None
        self.analog_channels = []
        self.digital_channels = []
        self.subsampling_rate = None

    def info(self):
        hw = model.get_hw_settings()
        return 'HIL hardware version: %s' % (hw,)

    def open(self):
        pass

    def close(self):
        pass

    def data_read(self):

        v1 = float(cp.read_analog_signal(name='V( Vrms1 )'))
        v2 = float(cp.read_analog_signal(name='V( Vrms2 )'))
        v3 = float(cp.read_analog_signal(name='V( Vrms3 )'))
        i1 = float(cp.read_analog_signal(name='I( Irms1 )'))
        i2 = float(cp.read_analog_signal(name='I( Irms2 )'))
        i3 = float(cp.read_analog_signal(name='I( Irms3 )'))
        p = float(cp.read_analog_signal(name='Pdc'))  # Note this is the AC power (fundamental)
        va = float(cp.read_analog_signal(name='S'))
        q = float(cp.read_analog_signal(name='Qdc'))
        pf = float(cp.read_analog_signal(name='k'))
        # f = cp.frequency

        dc_v = float(cp.read_analog_signal(name='V( V_DC3 )'))
        dc_i = float(cp.read_analog_signal(name='I( Ipv )'))

        datarec = {'TIME': time.time(),
                   'AC_VRMS_1': v1,
                   'AC_IRMS_1': i1,
                   'AC_P_1': p/3.,
                   'AC_S_1': va/3.,
                   'AC_Q_1': q/3.,
                   'AC_PF_1': pf,
                   'AC_FREQ_1': None,
                   'AC_VRMS_2': v2,
                   'AC_IRMS_2': i2,
                   'AC_P_2': p/3.,
                   'AC_S_2': va/3.,
                   'AC_Q_2': q/3.,
                   'AC_PF_2': pf,
                   'AC_FREQ_2': None,
                   'AC_VRMS_3': v3,
                   'AC_IRMS_3': i3,
                   'AC_P_3': p/3.,
                   'AC_S_3': va/3.,
                   'AC_Q_3': q/3.,
                   'AC_PF_3': pf,
                   'AC_FREQ_3': None,
                   'DC_V': dc_v,
                   'DC_I': dc_i,
                   'DC_P': dc_i*dc_v}

        return datarec

    def waveform_config(self, params):
        """
        Configure waveform capture.

        params: Dictionary with following entries:
            'sample_rate' - Sample rate (samples/sec)
            'pre_trigger' - Pre-trigger time (sec)
            'post_trigger' - Post-trigger time (sec)
            'trigger_level' - Trigger level
            'trigger_cond' - Trigger condition - ['Rising_Edge', 'Falling_Edge']
            'trigger_channel' - Trigger channel - ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']
            'timeout' - Timeout (sec)
            'channels' - Channels to capture - ['AC_V_1', 'AC_V_2', 'AC_V_3', 'AC_I_1', 'AC_I_2', 'AC_I_3', 'EXT']
        """
        self.wfm_sample_rate = params.get('sample_rate')
        self.wfm_pre_trigger = params.get('pre_trigger')
        self.wfm_post_trigger = params.get('post_trigger')
        self.wfm_trigger_level = params.get('trigger_level')
        self.wfm_trigger_cond = params.get('trigger_cond')
        self.wfm_trigger_channel = params.get('trigger_channel')
        self.wfm_timeout = params.get('timeout')
        self.wfm_channels = params.get('channels')  # SVP names

        self.analog_channels = []
        self.digital_channels = []
        # signals for capturing
        for c in self.wfm_channels:
            try:
                chan = wfm_typhoon_channels[c]
                if chan is not None:
                    # Create analog and digital channel lists
                    if wfm_typhoon_channel_type[chan] == 'analog':
                        self.analog_channels.append(chan)
                    else:
                        self.digital_channels.append(chan)
            except KeyError:
                self.ts.log_error('Not including channel: %s' % c)

        if len(self.digital_channels) > 0:
            self.channelSettings = [self.analog_channels, self.digital_channels]  # Typhoon names
        else:
            self.channelSettings = [self.analog_channels]  # Typhoon names

        simulationStep = cp.get_sim_step()
        hil_sampling_rate = 1./simulationStep
        if self.wfm_sample_rate != hil_sampling_rate:
            self.ts.log_warning('Waveform will be sampled at %s Samples/s because this is the simulation timestep '
                                'and then resampled to generate the waveform.' % hil_sampling_rate)
            self.subsampling_rate = hil_sampling_rate/self.wfm_sample_rate
            if type(self.subsampling_rate) != 'int':
                self.ts.log_warning('Subsampling HIL waveform factor is %s, but using integer %s to downsample data.' %
                                    (self.subsampling_rate, int(self.subsampling_rate)))
                self.subsampling_rate = int(self.subsampling_rate)

        self.triggerOffset = (self.wfm_pre_trigger/(self.wfm_pre_trigger+self.wfm_post_trigger))*100.
        self.numberOfSamples = int(hil_sampling_rate*(self.wfm_pre_trigger+self.wfm_post_trigger))
        if self.numberOfSamples > 32e6/len(self.analog_channels):
            self.ts.log_warning('Number of samples is not less than 32e6/numberOfChannels!')
            self.numberOfSamples = 32e6/len(self.analog_channels)  # technically this only counts for analog channels
            self.ts.log_warning('Number of samples set to 32e6/numberOfChannels!')
        elif self.numberOfSamples < 256:
            self.ts.log_warning('Number of samples is not greater than 256!')
            self.numberOfSamples = 256
            self.ts.log_warning('Number of samples set to 256.')
        elif self.numberOfSamples % 2 == 1:
            self.ts.log_warning('Number of samples is not even!')
            self.numberOfSamples += 1
            self.ts.log_warning('Number of samples set to %d.' % self.numberOfSamples)

        if wfm_typhoon_channel_type[wfm_typhoon_channels[self.wfm_trigger_channel]] == 'digital':
            self.captureSettings = [self.decimation, len(self.analog_channels), self.numberOfSamples, True]
            self.triggerSettings = ["Digital", wfm_typhoon_channels[self.wfm_trigger_channel], self.wfm_trigger_level,
                                    event_map[self.wfm_trigger_cond], self.triggerOffset]
        else:
            self.captureSettings = [self.decimation, len(self.analog_channels), self.numberOfSamples]
            self.triggerSettings = ["Analog", wfm_typhoon_channels[self.wfm_trigger_channel], self.wfm_trigger_level,
                                    event_map[self.wfm_trigger_cond], self.triggerOffset]

        # python list is used for data buffer
        self.capturedDataBuffer = []  # reset the data buffer

    def waveform_capture(self, enable=True, sleep=None):
        """
        Enable/disable waveform capture.
        """
        if enable:

            self.wfm_data = None  # used as flag in waveform_status()

            self.ts.log_debug('CaptureSettings: %s, triggerSettings: %s, channelSettings: %s, dataBuffer: %s'
                              % (self.captureSettings, self.triggerSettings, self.channelSettings,
                                 self.capturedDataBuffer))

            # start capture process and if everything ok, continue...
            if cp.start_capture(self.captureSettings,
                                self.triggerSettings,
                                self.channelSettings,
                                dataBuffer=self.capturedDataBuffer,
                                timeout=self.wfm_timeout):

                # DO NOT BLOCK ACCESS TO TYPHOON SO GRID AND SWITCH SETTINGS CAN BE CHANGED
                # countdown = self.wfm_timeout
                # while self.waveform_status() == 'ACTIVE':
                #     if countdown < 0:
                #         break
                #     else:
                #         countdown -= 1
                #         self.ts.log_debug('Capturing waveform. Status: %s. Timeout in %d seconds.' %
                #                           (self.waveform_status(), countdown))
                #         sleep(1)
                #

                pass

            else:
                self.ts.log_error('Did not start capture. CaptureSettings: %s, triggerSettings: %s, '
                                  'channelSettings: %s, dataBuffer: %s' % (self.captureSettings,
                                                                           self.triggerSettings,
                                                                           self.channelSettings,
                                                                           self.capturedDataBuffer))

    def waveform_status(self):
        # return INACTIVE, ACTIVE, COMPLETE
        if cp.capture_in_progress():
            stat = 'ACTIVE'
        # elif self.wfm_data is None:
        #     stat = 'INACTIVE'
        else:
            stat = 'COMPLETE'
        return stat

    def waveform_force_trigger(self):
        """
        Create trigger event with provided value.
        """
        self.triggerSettings = ["Forced"]
        self.waveform_capture(enable=True, sleep=None)

    def waveform_capture_dataset(self):
        if len(self.capturedDataBuffer) > 0:
            self.signalsNames, self.wfm_data, self.time_vector = self.capturedDataBuffer[0]
        else:
            self.ts.log_error('Did not capture data!')

        ds = dataset.Dataset()
        masterlist = self.analog_channels + self.digital_channels
        if len(self.signalsNames) == len(masterlist):
            ds.points.append('TIME')
            ds.data.append(self.time_vector[0::self.subsampling_rate])
            chan_count = 0
            for c in masterlist:
                ds.points.append(wfm_typhoon_channels[c])
                ds.data.append(self.wfm_data[chan_count][0::self.subsampling_rate])
                chan_count += 1

        else:
            self.ts.log_error('Number of channels returned from waveform capture is unexpected. '
                              'Expected %s. Got: %s' % (self.channelSettings, self.signalsNames))

        return ds


if __name__ == "__main__":
    import sys
    import time
    import numpy as np
    import math
    sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable/Lib/site-packages')
    sys.path.insert(0, r'C:/Typhoon HIL Control Center/python_portable')
    sys.path.insert(0, r'C:/Typhoon HIL Control Center')
    import typhoon.api.hil_control_panel as hil
    from typhoon.api.schematic_editor import model
    import os

    hil.set_debug_level(level=3)
    hil.stop_simulation()

    model.get_hw_settings()
    if not model.load(r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib/svpelab/Typhoon/ASGC.tse'):
        print "Model did not load!"

    if not model.compile():
        print "Model did not compile!"

    # first we need to load model
    hil.load_model(file=r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib'
                        r'/svpelab/Typhoon/ASGC Target files/ASGC.cpd')

    # we could also open existing settings file...
    hil.load_settings_file(file=r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib/'
                                r'svpelab/Typhoon/settings2.runx')

    # after setting parameter we could start simulation
    hil.start_simulation()

    # let the inverter startup
    sleeptime = 15
    for i in range(1, sleeptime):
        print ("Waiting another %d seconds until the inverter starts. Power = %f." %
               ((sleeptime-i), hil.read_analog_signal(name='Pdc')))
        time.sleep(1)

    '''
    Waveform capture
    '''
    simulationStep = hil.get_sim_step()
    print('Simulation time step is %f' % simulationStep)
    trigsamplingrate = 1./simulationStep
    pretrig = 0.5
    posttrig = 1.0
    trigval = 0.0
    trigtimeout = 5
    trigcondition = 'Falling edge'
    trigchannel = 'V( V_L1 )'
    #trigacqchannels = [['V( V_DC3 )', 'I( Ipv )', 'V( V_L1 )', 'I( Ia )'], ['S1_fb']]
    trigacqchannels = [['V( V_L1 )', 'V( V_L2 )', 'V( V_L3 )', 'I( Ia )', 'I( Ib )', 'I( Ic )']]
    n_analog_channels = 6
    save_file_name = r'D:/SVP/SVP 1.4.3 Directories 5-2-17/svp_energy_lab-loadsim/Lib/svpelab/Typhoon/waveform.mat'

    # signals for capturing
    channelSettings = trigacqchannels

    # cpSettings - list[decimation,numberOfChannels,numberOfSamples, enableDigitalCapture]
    numberOfSamples = int(trigsamplingrate*(pretrig+posttrig))
    print('Numer of Samples is %d' % numberOfSamples)
    if numberOfSamples > 32e6/n_analog_channels:
        print('Number of samples is not less than 32e6/numberOfChannels!')
        numberOfSamples = 32e6/n_analog_channels
        print('Number of samples set to 32e6/numberOfChannels!')
    elif numberOfSamples < 256:
        print('Number of samples is not greater than 256!')
        numberOfSamples = 256
        print('Number of samples set to 256.')
    elif numberOfSamples % 2 == 1:
        print('Number of samples is not even!')
        numberOfSamples += 1
        print('Number of samples set to %d.' % numberOfSamples)

    '''
    triggerSource - channel or the name of signal that will be used for triggering (int value or string value)
        Note:
        In case triggerType == Analog:
            triggerSource (int value) - value can be > 0 and <= "numberOfChannels" if we enter channel number.
            triggerSource (string value) - value is Analog signal name that we want to use for trigger source. Analog Signal
            name must be one of signal names from list of signals that we want to capture ("chSettings" list, see below).
        In case triggerType == Digital:
            triggerSource (int value) - value must be > 0 and maximal value depends of number of digital signals in loaded model
            triggerSource (string value) - value is Digital signal name that we want to use for trigger source.

    threshold - trigger threshold (float value)
        Note: "threshold" is only used for "Analog" type of trigger. If you use "Digital" type of trigger, you still
        need to provided this parameter (for example 0.0 )

    edge - trigger on "Rising edge" or "Falling edge"

    triggerOffset - Define the number of samples in percentage to capture before the trigger event (for example 20, if
        numberOfSamples is 100k, 20k samples before and 80k samples after the trigger event will be captured)
    '''

    # trSettings - list[triggerType,triggerSource,threshold,edge,triggerOffset]
    triggerSettings = ["Analog", trigchannel, trigval, trigcondition, (pretrig*100.)/(pretrig+posttrig)]
    # triggerSettings = ["Digital", 'S1_fb', trigval, trigcondition, (pretrig*100.)/(pretrig+posttrig)]
    # triggerSettings = ["Forced"]

    # python list is used for data buffer
    capturedDataBuffer = []


    captureSettings = [1, n_analog_channels, numberOfSamples]
    print captureSettings
    print triggerSettings
    print channelSettings
    print('Power = %0.3f' % hil.read_analog_signal(name='Pdc'))
    # if hil.read_digital_signal(name='S1_fb') == 1:
    #     print('Contactor is closed.')
    # else:
    #     print('Contactor is open.')

    # start capture process...
    if hil.start_capture(captureSettings,
                         triggerSettings,
                         channelSettings,
                         dataBuffer=capturedDataBuffer,
                         fileName=save_file_name,
                         timeout=trigtimeout):

        # #print hil.available_contactors()
        # print("Actuating S1 Contactor")
        # hil.set_contactor_control_mode('S1', swControl=True)
        # hil.set_contactor_state('S1', swState=False, executeAt=None)  # open contactor
        #
        # if hil.read_digital_signal(name='S1_fb') == 1:
        #     print('Contactor is closed.')
        # else:
        #     print('Contactor is open.')

        # when capturing is finished...
        while hil.capture_in_progress():
            pass

        # unpack data from data buffer
        (signalsNames, wfm_data, wfm_time) = capturedDataBuffer[0]

        subsampling_rate = 10
        print('Length of wfm_time = %s' % len(wfm_time))
        wfm_time = wfm_time[0::subsampling_rate]
        print('Length of wfm_time = %s' % len(wfm_time))

        # unpack data for appropriate captured signals
        # V_dc = wfm_data[0]  # first row for first signal and so on
        # i_dc = wfm_data[1]
        # V_ac = wfm_data[2]
        # i_ac = wfm_data[3]
        # contactor_trig = wfm_data[4]
        # import matplotlib.pyplot as plt
        # plt.plot(wfm_time, V_ac, 'b', wfm_time, i_ac, 'r', wfm_time, contactor_trig*100, 'k')
        # plt.show()

        print(len(wfm_data[0]))
        print(len(wfm_data[0][0::subsampling_rate]))

        V_1 = wfm_data[0][0::subsampling_rate]  # first row for first signal and so on
        V_2 = wfm_data[1][0::subsampling_rate]
        V_3 = wfm_data[2][0::subsampling_rate]
        I_1 = wfm_data[3][0::subsampling_rate]
        I_2 = wfm_data[4][0::subsampling_rate]
        I_3 = wfm_data[5][0::subsampling_rate]

        import matplotlib.pyplot as plt
        plt.plot(wfm_time, V_1, 'b', wfm_time, V_2, 'r', wfm_time, V_3, 'k',
                 wfm_time, I_1, 'b', wfm_time, I_2, 'r', wfm_time, I_3, 'k')
        plt.show()

        # hil.set_contactor_state('S1', swState=True, executeAt=None)

        # read the AC Power
        # for i in range(1, 10):
        #     print hil.read_analog_signal(name='Pdc')
        #     time.sleep(2)

    # stop simulation
    hil.stop_simulation()

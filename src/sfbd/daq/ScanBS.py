import logging
import socket
import datetime
from threading import Thread

import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

# PSI libraries for bsread
from bsread import dispatcher, source

# class for a fast recording of BS channels without any actuators
class ScanBS(QObject):
    """
    class to acquire data from bsread stream. the main work is placed in a thread, which emits
    pyqtSignals siginc and sigterm for its progress and temrination
    """

    siginc  = pyqtSignal(int, int)  # signal for increment
    sigterm = pyqtSignal(int)       # signal for termination

    def __init__(self, logger=None):

        QObject.__init__(self)

        self.program = 'ScanBS'
        self.version = '1.0.1'

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                            format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('BS Scan started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

        # get list of available channels for BSRead
        self.bschannellist = dispatcher.get_current_channels()

        self.bschannels=[]
        self.doAbort = False
        self.maxRetries = 1000
        self.ncount = 0
        self.data = {}

    # toggeling flag to abort run
    def abort(self):
        """
        function to terminate thread nicely if scan is running
        :return: None
        """
        self.doAbort = True

    def isBSChannel(self, channel):
        """
        checks whether a requested channel is in the list of available bsread channnels
        :param channel:
        :return:
        """
        for ele in self.bschannellist:
            if channel.upper() == ele['name']:
                return ele
        return None

    def run(self, channels=[], nsample=1):
        """
        Routine to launch a time recording of bsread channels. the function launches a thread for the actual measurement
        :param channels: list of channel names
        :param nsample: number of samples
        :return: none
        """
        self.bschannels.clear()
        # check whether the requested channels are available
        for channel in channels:
            bschannel = self.isBSChannel(channel)
            if bschannel is not None:     # if channel does notexist it is excluded
                self.bschannels.append(bschannel)
            else:
                self.logger.warning('Channel %s not supported by BSREAD and will be excluded.' % channel)
        # allocate memory to hold information
        self.ncount = nsample
        ndim = [nsample]
        self.data.clear()
        self.data['Shot:ID'] = np.ndarray(ndim, dtype='uint64')
        for ele in self.bschannels:
            if ele['shape'][0] > 1:    # non scalar value
                self.data[ele['name']] = np.ndarray(ndim+ele['shape'], dtype=ele['type'])
            else:
                self.data[ele['name']] = np.ndarray(ndim, dtype=ele['type'])
        # clear flags for the run
        self.doAbort = False
        # start the thread
        Thread(target=self.runner).start()


    def runner(self):
        """
        thread to do actually measurement. The thread is aborted if the variable self.doAbort is set to True
        :return: none (but emits signals to report on progress)
        """
        iret = 0      # count for number of retries
        nret = self.maxRetries
        icount = 0
        isignal = int(np.round(self.ncount * 0.1))  # estimate for 10% of measurement done
        self.siginc.emit(0, self.ncount)    # emit initial signal for start of measurement
        self.logger.info('Scan Thread started')
        with source(channels=self.bschannels) as stream:
            while icount < self.ncount and not self.doAbort:
                msg = stream.receive()  # read BS
                valid = True
                for chn in self.bschannels:  # check that all requested data are valid
                    if msg.data.data[chn['name']].value is None:
                        iret += 1
                        valid = False
                        if iret > nret:
                            self.doAbort = True
                        break
                if not valid:
                    continue

                # dataset is valid
                iret = 0   # reset counter of retries
                # save the data
                self.data['Shot:ID'][icount] = msg.data.pulse_id
                for i, ele in enumerate(self.bschannels):
                    if len(self.data[ele['name']].shape) > 1:
                        self.data[ele['name']][icount, :] = np.array(msg.data.data[ele['name']].value)
                    else:
                        self.data[ele['name']][icount] = msg.data.data[ele['name']].value
                icount += 1
                if (icount % isignal) == 0:
                    self.siginc.emit(icount, self.ncount)
        if self.doAbort:
            self.sigterm.emit(-1)  # signal for indicating an error/abort etc
        else:
            self.sigterm.emit(0)   # scan completed normally
        self.logger.info('Scan Thread is exiting...')

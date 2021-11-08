import logging
import socket
import datetime
from threading import Thread
import time
import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

# PSI libraries epics interface
from epics import PV


# class for a fast recording of BS channels without any actuators
class ScanPV(QObject):
    """
     class to acquire data from bsread stream. the main work is placed in a thread, which emits
     pyqtSignals siginc and sigterm for its progress and temrination
     """
    siginc  = pyqtSignal(int, int)  # signal for progress
    sigterm = pyqtSignal(int)  # signal for termination

    def __init__(self, logger=None):

        QObject.__init__(self)

        self.program = 'ScanPV'
        self.version = '1.0.1'

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                                format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('PV Scan started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

        # get list of available channels for BSRead
        self.pvchannels = []
        self.doAbort = False
        self.maxRetries = 1000
        self.aqrate=0.01  #  10 ms second for 100 Hz reading
        self.ncount = 0
        self.data = {}

    def abort(self):
        """
         function to terminate thread nicely if scan is running
         :return: None
         """
        self.doAbort = True

    def run(self, channels=[], nsample=1, freq=100):
        """
          Routine to launch a time recording of PV channels. the function launches a thread for the actual measurement
          :param channels: list of channel names
          :param nsample: number of samples
          :param freq: requested frequency
          :return: none
          """
        self.pvchannels.clear()
        # check whether the requested channels are available
        self.ncount = nsample
        self.aqrate = 1./freq
        self.data.clear()
        ndim = [nsample]

        # check for false channels which are giving none
        pvchannels = [PV(pv) for pv in channels]
        con = [pv.wait_for_connection(timeout=0.5) for pv in pvchannels]
        for i, val in enumerate(con):
            if val == True:
                self.pvchannels.append(pvchannels[i])
            else:
                self.logger.warning('Channel %s cannot access by PV and will be excluded.' % pvchannels)
                print('Cannot connect to PV:', pvchannels[i].pvname)

        # do a quick reading to get data size
        for i, pv in enumerate(self.pvchannels):
            val = pv.get(timeout=0.2)
            if np.isscalar(val):
                self.data[pv.pvname] = np.ndarray(ndim, dtype=np.float)
            else:
                self.data[pv.pvname] = np.ndarray(ndim + [len(val)], dtype=np.float)
        self.doAbort = False
        Thread(target=self.runner).start()

    def runner(self):
        iret = 0
        nret = self.maxRetries
        icount = 0
        isignal = int(np.round(self.ncount * 0.1))

        self.siginc.emit(0, self.ncount)
        self.logger.info('Scan Thread started')

        while icount < self.ncount and not self.doAbort:
            msg = [pv.get(timeout=0.1) for pv in self.pvchannels]
            valid = True
            for chn in msg:
                if chn is None:
                    iret += 1
                    valid = False
                    if iret > nret:
                        self.doAbort = True
                    break
            if not valid:
                time.sleep(self.aqrate)
                continue

            # dataset is valid
            iret = 0  # reset counter of retries
            for i, val in enumerate(msg):
                if np.isscalar(val):
                    self.data[self.pvchannels[i].pvname][icount] = val
                else:
                    self.data[self.pvchannels[i].pvname][icount, :] = val

            icount += 1
            if (icount % isignal) == 0:
                self.siginc.emit(icount, self.ncount)
            time.sleep(self.aqrate)
        if self.doAbort:
            self.sigterm.emit(-1)
        else:
            self.sigterm.emit(0)
        self.logger.info('Scan Thread is exiting...')
import logging
import socket
import datetime
import time
import sys
from threading import Thread

import numpy as np

from PyQt5.QtCore import QObject, pyqtSignal

# PSI libraries for bsread
from bsread import dispatcher, source

# add other classes
sys.path.append('/sf/bd/packages/SFBD/src')
import sfbd.daq.PVAccess as PVAccess
import sfbd.daq.ActuatorPV as Actuator
import sfbd.interface.snapshot as Snap
import sfbd.interface.save as Save

# class for a fast recording of BS channels without any actuators
class ScanBS(QObject):
    """
    class to acquire data from bsread stream. the main work is placed in a thread, which emits
    pyqtSignals siginc and sigterm for its progress and temrination
    """

    siginc  = pyqtSignal(int, int)  # signal for increment
    sigterm = pyqtSignal(int)       # signal for termination

    def __init__(self, logger=None,program='SFBD_ScanBS',version='1.0.1',snapfile=None):

        QObject.__init__(self)

        self.program = program
        self.version = version

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
        self.ncount = 0   # total number of measurements
        self.nsample = 0  # number of samples
        self.nstep = 0    # number of steps (0 = time recording)
        self.data = {}
        self.actuator = Actuator.ActuatorPV(self.logger) 
        self.preaction= PVAccess.PVAccess(self.logger)
        self.epicsread= PVAccess.PVAccess(self.logger)
        self.preactionVal={}

        if not snapfile:
            snapfile='/sf/data/applications/snapshot/req/op/SF_settings.req'
        self.logger.info('Snapshot request file: %s' % snapfile)
        self.Snap = Snap.snapshot(snapfile)
        self.snapval={}
        self.snapmval={}
        self.Save=Save.Save(self.logger,self.program,self.version)

    def setSnapshot(self,filename):
        self.logger.info('Snapshot request file: %s' % snapfile)
        self.Snap.openRequestFile(filename)

    # toggeling flag to abort run
    def abort(self):
        """
        function to terminate thread nicely if scan is running
        :return: None
        """
        self.doAbort = True
        if not self.actuator is None:
            self.actuator.abort()
        self.preaction.restore()

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

        
    def run(self, channels=[], nsample=1, *args, **kwargs):
        """
        Routine to launch a time recording of bsread channels. the function launches a thread for the actual measurement
        :param channels: list of bs channel names
        :param nsample: number of samples
        :param kwargs: option keyword=value
        :return: True/False if there were problems with the initialization
        """
        
        # preaction
        self.preactionVal=kwargs.get('preaction',{})
        status=self.preaction.store(self.preactionVal.keys())
        if not status:
            return status

        # actuator
        act = kwargs.get('actuator',{})
        timeout=kwargs.get('timeout',1.0)
        settle=kwargs.get('settle',1.0)
        nstep=kwargs.get('nstep',0)
        if not self.actuator.init(act,timeout,settle,nstep):
            self.sigterm.emit(-3)
            return False
   
        # define sensor
        self.bschannels.clear()
        epicschannels=[]
        # check whether the requested channels are available
        for channel in channels:
            bschannel = self.isBSChannel(channel)
            if bschannel is not None:     # if channel does notexist it is excluded
                self.bschannels.append(bschannel)
            else:
                epicschannels.append(channel)
        echn = kwargs.get('epics',[])
        for channel in echn:
            epicschannels.append(channel)
        if not self.epicsread.store(epicschannels):
            return False

        # allocate memory to hold information
        self.nsample=nsample  # time recording
        self.nstep = self.actuator.nsteps
        if self.actuator.isActuator:
            self.ncount=self.nstep*self.nsample
            ndim=[self.nstep,self.nsample]  
            self.logger.info('Data allocation for scan')
        else:
            self.ncount=self.nsample
            ndim=[self.nsample]
            self.logger.info('Data allocation for time recording')

        self.data.clear()
        self.data['Shot:ID'] = np.ndarray(ndim, dtype='uint64')
        for ele in self.bschannels:
            print('BS Channel:',ele['name'])
            if ele['shape'][0] > 1:    # non scalar value
                self.data[ele['name']] = np.ndarray(ndim+ele['shape'], dtype=ele['type'])
            else:
                self.data[ele['name']] = np.ndarray(ndim, dtype=ele['type'])

        for pv in self.epicsread.pvchannels:
            print('EPICS Channel',pv.pvname)
            dtype = np.float
            if 'enum' in pv.type or 'int' in pv.type or 'bool' in pv.type:
                dtype=np.int
            if pv.count == 1:
                self.data[pv.pvname] = np.ndarray(ndim, dtype=dtype)
            else:
                self.data[pv.pvname] = np.ndarray(ndim+[pv.count], dtype=dtype)

        # clear flags for the run
        self.doAbort = False
        # start the thread
        Thread(target=self.runthread).start()
        self.snapval,self.snapmval=self.Snap.getSnapValues()
        self.logger.info('Snapshot acquired')
        return True

    def runthread(self):
        """
        Wrapper function to catch the erro rif a stream cannot be established
        :return:
        """

        try:
            self.runner()
        except:
            self.logger.error("Cannot establish BSRead stream")
            self.abort()           # stop also thread of actuator if defined
            self.sigterm.emit(-2)  # signal for indicating for a failed stream request or other error, crashingthe program

    def runner(self):
        """
        thread to do actually measurement. The thread is aborted if the variable self.doAbort is set to True
        Note that only here are PV values set. 
        :return: none (but emits signals to report on progress)
        """
        iret = 0      # count for number of retries
        icount = 0
        istep = 0
        isample = 0
        isignal = int(np.round(self.ncount * 0.1))  # estimate for 10% of measurement done
        lastplot = 0

        # do preaction item
        if len(self.preactionVal.keys()) > 0:
            self.logger.info('Setting preaction values')
            self.preaction.write(self.preactionVal)

        self.siginc.emit(0, self.ncount)    # emit initial signal for start of measurement
        self.logger.info('Scan Thread started')

        # get stream  first
        with source(channels=self.bschannels) as stream:
            # set first actuator step 
            self.actuator.increment()
            while icount < self.ncount and not self.doAbort:
 
               # read BS stream
                msg = stream.receive() 
                BStime = msg.data.global_timestamp+msg.data.global_timestamp_offset*1e-9
                # actuator is still busy
                if self.actuator.busy or BStime <  self.actuator.settime:
                    continue

                # check if message is valid
                valid = True
                for chn in self.bschannels:  # check that all requested data are valid
                    if msg.data.data[chn['name']].value is None:
                        iret += 1
                        valid = False
                        if iret > self.maxRetries:
                            self.doAbort = True
                            self.logger.error('Maximum tries of reading bsstream exceeded.')
                            self.sigterm.emit(-4)  # maximum number of tries exceeded
                            continue
                if not valid:
                    continue
                iret = 0

                # read epics channnels
                epicsval = self.epicsread.read()

                # save the data for time recording or scan
                if self.actuator.isActuator:
                    self.data['Shot:ID'][istep,isample] = msg.data.pulse_id
                    for i, ele in enumerate(self.bschannels):
                        if len(self.data[ele['name']].shape) > 2:
                            self.data[ele['name']][istep,isample, :] = np.array(msg.data.data[ele['name']].value)
                        else:
                            self.data[ele['name']][istep,isample] = msg.data.data[ele['name']].value
                    for i, ele in enumerate(self.epicsread.pvchannels):
                        if ele.count > 1:
                            self.data[ele.pvname][istep,isample,:] = np.array(epicsval[i])
                        else:
                            self.data[ele.pvname][istep,isample] = epicsval[i]
                else:
                    self.data['Shot:ID'][isample] = msg.data.pulse_id
                    for i, ele in enumerate(self.bschannels):
                        if len(self.data[ele['name']].shape) > 1:
                            self.data[ele['name']][isample, :] = np.array(msg.data.data[ele['name']].value)
                        else:
                            self.data[ele['name']][isample] = msg.data.data[ele['name']].value
                    for i, ele in enumerate(self.epicsread.pvchannels):
                        if ele.count > 1:
                            self.data[ele.pvname][isample,:] = np.array(epicsval[i])
                        else:
                            self.data[ele.pvname][isample] = epicsval[i] 

                # increase counter and increment actuator if needed
                icount  += 1
                isample += 1
                if (isample % self.nsample)==0:
                    isample=0
                    istep+=1
                    self.actuator.increment()
                if (icount % isignal) == 0:
                    lastplot = icount
                    self.siginc.emit(icount, self.ncount)

        # make sure that the last step is plot
        if (lastplot<self.ncount):
            self.siginc.emit(self.ncount,self.ncount)

        if self.doAbort:
            self.sigterm.emit(-1)  # signal for abort
        else:
            self.sigterm.emit(0)   # scan completed normally
        self.logger.info('Restoring Actuators and Preaction Items...')
        self.actuator.terminate()
        time.sleep(0.5)
        self.preaction.restore()

        self.logger.info('Scan Thread is exiting...')


    def save(self,derived={}):
        self.Save.open()
        self.Save.writeSnap(self.snapval)
        self.Save.writeSnap(self.snapmval)
        self.Save.writeData(self.data)        
        self.Save.writeActuator(self.actuator)
        self.Save.close()
        return self.Save.filename

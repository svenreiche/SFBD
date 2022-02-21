import logging
import socket
import datetime
import time
from threading import Thread

from epics import PV
import PVAccess

class ActuatorPV:
    """
    class to scan PV values via a thread.
    """
    def __init__(self, logger=None):

        self.program = 'SFBD/ActuatorPV'
        self.version = '1.0.1'

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                                format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('Actuator started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

        self.doAbort = False
        self.busy = False
        self.isActuator = False  # true if actuators are actually used.
        self.status = -1  # not initialized
            # get list of available channels for BSRead
        self.pvchannels = []
        self.actuators={}
        self.backup=PVAccess()
        self.settle=0.
        self.timeout=1.
        self.hasTimeout = False

    def abort(self):
        """
        thread save routine to abort current thread for setting actuators and sets the initial values
        :return:
        """
        self.doAbort=True
        self.terminate()

    def terminate(self):
        """
        Set all PV channels to initial values
        :return: None
        """
        self.status=-1
        if not self.isActuator:
            self.backup.restore()
        
    def init(self, pvchannels=[], config={},timeout=1.,settle=0.):
        """
        function to define the actuator channels and set-up the connection
        :param channels: list of channels involved
        :param config: dictionary with setvalues, readback and tolerance
        :return: success (True/False)
        """
        if len(pvchannel) == 0:
            self.isActuator = False
            return True


        self.settle = settle
        self.timeout=timeout
        self.pvchannels=pvchannels

        if not self.backup.store(pvchannels):
            return False
        self.actuators.clear()
        nsteps=-1
        for i,pname in enumerate(self.pvchannels):
            pv=self.backup.pvchannels[i]   # the connection has been already establish in PVaccess
            if not pname in config.keys():
                self.logger.error('Cannot find actuator definition for pv: %s' % pname)
                return False
            if 'val' not in config[pname].keys():
                self.logger.error('Cannot find values for pv: %s' % pname)
                return False
            val = config[pname]['val']
            nlen = len(val)
            if nsteps < 0:
                nsteps = nlen
            elif not nlen == nsteps:
                self.logger.error('Mismatch in step count for pv: %s' % pname)
                return False
            pvrb = None
            tol = 0
            if  'readback' in config[pname].keys():
                pvrb = PV(config[pname]['readback'])
                con = pvrb.wait_for_connection(timeout=0.5)
                if con is False:
                    self.logger.error('Cannot connect to readback pv: %s' % config[pname]['readback'])
                    return False
                if not 'tol' in config[pname].keys():
                    self.logger.error('Tolerance for readback values not defined')
                    return False
            self.logger.info('Adding PV: %s to actuator list' % pname)
            self.actuators[pname]={'PV':pv,'val':val,'PVRB':pvrb,'tol':tol}

        self.isActuator = True
        self.nsteps = nsteps
        self.isteps=-1
        self.status = 0   # initialized
        self.busy=False
        return True

    def setActuator(self):
        """
        Set the setvalues of all actuators
        :return: none
        """
        if self.isteps<0:
            return
        for ele in self.actuators:
            ele['pv'].put(ele['val'][self.isteps])

    def checkReadback(self):
        """
        Check if current readback values agrees with setvalues within the given tolerance
        :return: True if all are within the tolerance or False otherwise
        """
        valid = True
        for ele in self.actuators:
            if not ele['PVRB'] is None:
                val=ele['PVRB'].get()
                diff = np.abs(val- ele['val'][self.isteps])
                if diff > ele['tol']:
                    valid = False
        return valid

    def increment(self):
        """
        Function to launch thread for setting a new setvalue
        :return: True if a thread could be started, False otherwise
        """
        if self.busy:
            return False
        self.busy=True
        self.hasTimeout = False
        self.isteps+=1
        if self.isteps < self.nsteps and not self.doAbort and self.status >0:
            Thread(target=self.setthread).start()
            return True
        return False


    def setthread(self):
        """
        Thread to set a new set value and wait for timeout and settletime
        The situation can be polled. If busy is active then the thread is still running.
        If a timeout has occured than the internal flag hasTimeout is set to True
        :return:
        """
        self.setActuator()
        waiting=True
        start=time.time()
        self.hasTimeout = False
        while waiting:
            if self.doAbort:
                self.busy=False
                return
            if self.checkReadback():
                waiting = False
            if waiting:
                dt = time.time()-start
                if dt > self.timeout:
                    self.hasTimeout = True
                    waiting = False
                else:
                    time.sleep(0.1)
        if self.settle>0:
            time.sleep(self.settle)
        self.busy = False
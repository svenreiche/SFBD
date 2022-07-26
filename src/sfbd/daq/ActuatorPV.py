import sys
import logging
import socket
import datetime
import time
from threading import Thread
import numpy as np

from epics import PV

#
#  remove return in self.temrinate()
#  uncomment setting of PV in self.setActuator()
#  check timeout and settle time functionality
#


sys.path.append('/sf/bd/packages/SFBD/src')
import sfbd.daq.PVAccess as PVAccess

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


        self.actuators={}
        self.backup=PVAccess.PVAccess(self.logger)

        self.settle=0.
        self.timeout=1.
        self.nsteps = 0
        self.hasTimeout = False
        self.settime=1e12


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
        print('terminating actuators')
        if self.isActuator:
            self.backup.restore()
        
    def init(self, actuator={},timeout=1.,settle=0,nsteps=0):
        """
        function to define the actuator channels and set-up the connection
        :param actuator: dictionary to hold actuator definition
        :param timeout: timeout in second
        :param settle: settle time in second
        :param nsteps: steps of actuators
        :return: success (True/False)
        """
        if len(actuator.keys()) == 0:
            self.isActuator = False
            self.nsteps=0
            self.isteps=-1
            self.settime=-1.
            return True

        self.actuators=actuator
        self.settle = settle
        self.timeout=timeout
        self.nsteps=nsteps
        self.settime = 1e12 # enforce waiting for first actuator set procedure

        # get backup of actuator
        if not self.backup.store(self.actuators.keys()):
            print('cannot read actuator;')
            return False

        print('reading current actuator values')
        for i,key in enumerate(self.actuators.keys()):
            self.actuators[key]['PV']=self.backup.pvchannels[i]  
            print('actuator:',key, ' with steps',self.nsteps)
            val = np.linspace(self.actuators[key]['Start'],self.actuators[key]['End'],num=self.nsteps)
            if 'Relative' in self.actuators[key].keys():
                if self.actuators[key]['Relative']:
                    val += self.backup.refval[i]
            self.actuators[key]['val']=val
            pvrb = None
            if 'Readback' in self.actuators[key].keys():
                if len(self.actuators[key]['Readback']) > 3 :
                    pvrb = PV(self.actuators[key]['Readback'])
                    con = pvrb.wait_for_connection(timeout=0.5)
                    if con is False:
                        self.logger.error('Cannot connect to readback pv: %s' % self.actuators[key]['Readback'])
                        return False               
                    if not 'Tolerance' in self.actuators[key].keys():
                        self.logger.error('Tolerance for actuator readback not defined. Setting it to 0.')
                        self.actuators[key]['Tolerance']=0
            self.actuators[key]['PVRB']=pvrb 
            self.logger.info('Adding PV: %s to actuator list' % key)

        self.isActuator = True
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
        
        for key in self.actuators.keys():
            print('#### Actuator:', key,' set to',self.actuators[key]['val'][self.isteps], '(Step:',self.isteps+1,'of',self.nsteps,')')
            self.actuators[key]['PV'].put(self.actuators[key]['val'][self.isteps])

    def checkReadback(self):
        """
        Check if current readback values agrees with setvalues within the given tolerance
        :return: True if all are within the tolerance or False otherwise
        """
        valid = True
        for key in self.actuators.keys():
            if not self.actuators[key]['PVRB'] is None:
                val=self.actuators[key]['PVRB'].get()
                diff = np.abs(val- self.actuators[key]['val'][self.isteps])
                if diff > self.actuators[key]['Tolerance']:
                    valid = False
        return valid

    def increment(self):
        """
        Function to launch thread for setting a new setvalue
        :return: True if a thread could be started, False otherwise
        """
        if not self.isActuator:
            return True
        if self.busy:
            return False
        self.busy=True
        self.hasTimeout = False
        self.isteps+=1
        if self.isteps < self.nsteps and not self.doAbort and self.status == 0:
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
        self.settime=time.time()
        self.busy = False

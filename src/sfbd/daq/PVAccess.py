import logging
import socket
import datetime
from epics import PV

class PVAccess:
    """
    class to control access to PVs for seen to be written to. This is either to preserve a setting and restore later or
    as an active part of the actuator class of this package
    """
    def __init__(self, logger=None):

        self.program = 'SFBD/PVAccess'
        self.version = '1.0.1'

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                                format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('PVAccess started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

            # get list of available channels for BSRead
        self.pvchannels = []
        self.refval = None
        self.hasRestore = False

    def store(self, channels=[]):
        """
        function to establish connection to the PV and store its values
        :param channels: list of PV names
        :return: success (True/False)
        """
        self.pvchannels.clear()
        if len(channels) == 0:
            return True
        pvchannels = [PV(pv) for pv in channels]
        con = [pv.wait_for_connection(timeout=0.5) for pv in pvchannels]
        status = True
        for i, val in enumerate(con):
            if val == True:
                self.pvchannels.append(pvchannels[i])
            else:
                self.logger.warning('Channel %s cannot access by PV and will be excluded.' % pvchannels)
                status = False

        if status is False:
            self.logger.error('Cannot connect to requested channels. Abort PVAccess')
            return False
        self.logger.info('Initial acquisition of PV channels for restoring them after measurement')
        self.refval = [pv.get() for pv in self.pvchannels]
        self.hasRestore = True
        return status

    def restore(self):
        """
        function to restore values, previously saved with the store function
        :return: None
        """
        if not self.hasRestore:
            return
        if len(self.pvchannels) == 0:
            return
#        self.logger.info('Restoring PV Channels...')
        for i,pv in enumerate(self.pvchannels):
            print('#### Actuator/Preaction',pv.pvname,' restored to',self.refval[i])
            pv.put(self.refval[i])

    def read(self):
        """
        function to read group of stored PV channels
        :return: list of pv values
        """
        return [pv.get() for pv in self.pvchannels]

    def write(self, values):
        """
        function to write new set values for the pv channels
        :param values: dictionary of pvnames with their values
        :return: None
        """
        for pv in self.pvchannels:
            if pv.pvname in values.keys():
                print('Setting PV',pv.pvname,'to value',values[pv.pvname])
                pv.put(values[pv.pvname])

    def names(self):
        """
        function to return the list of PV names currently defined
        :return: stirng list of PV-names
        """
        return [pv.pvname for pv in self.pvchannels]

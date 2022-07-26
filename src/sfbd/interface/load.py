import sys
import os
import datetime
import h5py

# add other classes
#sys.path.append('/sf/bd/packages/SFBD/src')

class Load:
    def __init__(self, logger = None, program = 'SFBD', version = 'v1.0.0'):

        self.program = program
        self.version = version
        self.author ='S. Reiche'
        self.file = None
        

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                            format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('Load class started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

    
    def open(self,filename):
        self.file = h5py.File(filename, "r")

    def close(self):
        if self.file is not None:
            self.file.close()
        self.file = None
 
    def loadSnap(self):
        snap={}
        for key1 in self.file['experiment'].keys():
            for key2 in self.file['experiment'][key1].keys():
                val = self.file['experiment'][key1][key2][()]
                snap[key1+':'+key2]={'val':val}
        return snap

    def loadData(self,scanrun=1):
        run='scan_%d' % scanrun
        data = {} 
        for key1 in self.file[run]['data'].keys():
            for key2 in self.file[run]['data'][key1].keys():
                val = self.file[run]['data'][key1][key2][()]
                data[key1+':'+key2]=val
        return data

    def loadActuator(self,scanrun=1):
        run='scan_%d' % scanrun
        data = {} 
        if 'actuators' in self.file[run]['method'].keys():
            for key1 in self.file[run]['method']['actuators'].keys():
                for key2 in self.file[run]['method']['actuators'][key1].keys():
                    val = self.file[run]['method']['actuators'][key1][key2][()]
                    data[key1+':'+key2]={'val':val}
        return data


 

        
   





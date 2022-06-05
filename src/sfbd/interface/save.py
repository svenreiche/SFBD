import sys
import os
import datetime
import h5py

# add other classes
#sys.path.append('/sf/bd/packages/SFBD/src')

class Save:
    def __init__(self, logger = None, program = 'SFBD', version = 'v1.0.0'):

        self.program = program
        self.version = version
        self.author ='S. Reiche'
        self.filename=None
        self.file = None
        

        if logger == None:
            logging.basicConfig(level=logging.INFO,
                            format='%(levelname)-8s %(message)s')
            self.logger = logging.getLogger(self.program)
            self.logger.info('Save class started at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.logger.info('Version: %s ' % self.version)
            self.logger.info('Host: %s' % socket.gethostname())
        else:
            self.logger = logger

    

    def open(self):
        year = datetime.datetime.now().strftime('%Y')
        month = datetime.datetime.now().strftime('%m')
        day = datetime.datetime.now().strftime('%d')

        path = '/sf/data/measurements/%s' % year
        if not os.path.exists(path):
            os.makedirs(path)
        path = '%s/%s' % (path,month)
        if not os.path.exists(path):
            os.makedirs(path)
        path = '%s/%s' % (path,day)
        if not os.path.exists(path):
            os.makedirs(path)
        datetag = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
        self.filename=('%s/%s_%s' % (path, self.program.replace(' ','_'), datetag))
        self.file = h5py.File(self.filename+'.h5', "w")

        # meta data header               
        dt = h5py.special_dtype(vlen=bytes)
        dset=self.file.create_dataset('general/user',(1,),dtype=dt)
        dset[0]=os.getlogin()
        dset=self.file.create_dataset('general/application',(1,),dtype=dt)
        dset[0]=self.program
        dset=self.file.create_dataset('general/author',(1,),dtype=dt)
        dset[0]=self.author
        dset=self.file.create_dataset('general/version',(1,),dtype=dt)
        dset[0]=self.version
        dset=self.file.create_dataset('general/created',(1,),dtype=dt)
        dset[0]=str(datetime.datetime.now())


    def close(self):
        if self.file is not None:
            self.file.close()
        self.file = None
 

    def writeSnap(self,val):
        for key in val.keys():
            name=key.split(':')
            if 'value' in val[key].keys():
                data=val[key]['value']
            elif 'val' in val[key].keys():
                data=val[key]['val']
            else:
                continue
            dset=self.file.create_dataset('experiment/%s/%s' % (name[0],name[1]),data=[data])
            dset.attrs['system']=self.getSystem(name[0])
            dset.attrs['units']='unknown'

    
    def writeData(self, data, scanrun=1):
        if not 'Shot:ID' in data.keys():
            return
        shape = data['Shot:ID'].shape
        ndim = len(shape)
        nsam = shape[-1]
        nrec = 0
        if ndim > 1:
            nrec = shape[:-1][0]
        self.file.create_dataset("scan_%d/method/records" % scanrun,data=[nrec])
        self.file.create_dataset("scan_%d/method/samples" % scanrun,data=[nsam])
        self.file.create_dataset("scan_%d/method/dimension" % scanrun,data=[ndim])
        self.file.create_dataset("scan_%d/method/reducedData" % scanrun,data=[0])  # indicating that there is at least a 2D array for scalar data
        # write the sensor raw value
        for ele in data.keys():
            name=ele.split(':')
            dset=self.file.create_dataset('scan_%d/data/%s/%s' % (scanrun, name[0], name[1]), data=data[ele])
            dset.attrs['system'] = self.getSystem(name[0])
            dset.attrs['units'] = 'unknown'


    def writeActuator(self,act,scanrun=1):
        dt = h5py.special_dtype(vlen=bytes)
        dset=self.file.create_dataset("scan_%d/method/type" % scanrun,(1,),dtype=dt)
        if act.isActuator:
            dset[0]='Scan'        
        else:
            dset[0]='Time Recording'
        for ele in act.actuators.keys():
            name=ele.split(':')
            dset=self.file.create_dataset("scan_%d/method/actuators/%s/%s" % (scanrun,name[0],name[1]),data=act.actuators[ele]['val'])
            dset.attrs['system']=self.getSystem(name[0])
            dset.attrs['units']='unknown'

        
    def getSystem(self,name):
        if len(name) > 11:
            tag=name[8:9]
            fulltag=name[8:12]
        else:
            tag=''
            fulltag=''
        sys='Unknown'
        if tag =='P':
            sys='Photonics'
        if tag =='D':
            sys='Diagnostics'
        if fulltag =='DSCR':
            sys='Camera'
        if tag == 'R':
            sys='RF'
        if tag == 'M':
            sys='Magnets'
        if tag == 'U':
            sys='Undulator'
        return sys




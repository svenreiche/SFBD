import datetime
from snapshot.ca_core import Snapshot

class snapshot:
    def __init__(self,filename=None,savepath='/sf/data/applications/snapshot/'):

        self.filename = filename
        self.savepath = savepath
        if not self.filename:
            self.openRequestFile(self.filename)


    def openRequestFile(self,filename):
        self.filename = filename
        self.rootname=self.filename.split('/')[-1]
        req_file = SnapshotReqFile('./test.req', macros=macros)
        pvs_list = req_file.read()
        print(pvs_list)


    def open(self,root,pathreq='/sf/data/applications/SFBD/snapshot-config/'):

        self.root = 'SFBD_'+root
        self.pathreq = pathreq
        if not self.pathreq[-1] == '/':
            self.pathreq += '/'
        self.pathsave =
        self.snap = Snapshot(self.pathreq+self.root+'.req',{'Test':'Tres'})
        self.lastSaved.clear()


    def save(self,labels=[],comment="Generated by SFBD-Package"):
        if self.snap is None:
                return None

        datetag = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file = self.pathsave+self.root+'_'+datetag+'.snap'
        filel = self.pathsave+self.root+'_latest.snap'
        sts, pvs_sts = self.snap.save_pvs(file,force=False,symlink_path=filel,labels=labels,comment=comment)
        if 'ok' in sts.name:
            self.lastSaved.append(file)
            return file
        return None







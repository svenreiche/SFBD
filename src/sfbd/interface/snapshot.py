import datetime
from snapshot.ca_core import Snapshot

class snapshot:
    def __init__(self, request=None):
        self.snap = None
        if not request:
            return
        self.root = 'SFBD_'+request
        self.pathreq = '/sf/data/applications/SFBD/snapshot-config/'
        self.pathsave = '/sf/data/applications/snapshot/'
        self.snap = Snapshot(self.pathreq+self.root+'.req',{'Test':'Tres'})
        self.lastSaved = []   # files which have been saved already

    def save(self):
        if self.snap is None:
                return None

        datetag = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file = self.pathsave+self.root+'_'+datetag+'.snap'
        filel = self.pathsave+self.root+'_latest.snap'
        sts, pvs_sts = self.snap.save_pvs(file,force=False,symlink_path=filel)
        if 'ok' in sts.name:
            self.lastSaved.append(file)
            return file
        return None







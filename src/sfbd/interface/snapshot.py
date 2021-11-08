from snapshot.ca_core import Snapshot

class snapshot:
    def __init__(self, request=None):
        self.snap = None
        if not request:
            return
        self.pathreq = '/sf/data/applications/SFBD/snapshot-config/'
        self.pathroot = '/sf/data/applications/snapshot/SFBD'
        self.snap = Snapshot(self.pathreq+request+'.req',{'Test':'Tres'})
        self.lastSaved = []   # files which have been saved already

    def save(self,filebase):
        if self.snap is None:
                return
        file = self.pathroot+filebase+'.snap'
        filelatest = self.pathroot+filebase+'_latest.snap'
        self.snap.save_pvs(file,force=True,symlink_path=filelatest)






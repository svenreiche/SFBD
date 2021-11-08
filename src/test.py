import sfbd.interface.snapshot as snap
import time

sn = snap.snapshot('test')
time.sleep(5)
sn.save()



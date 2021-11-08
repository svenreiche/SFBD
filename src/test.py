import sfbd.daq.ScanBS as Scan


myscan=Scan.ScanBS()
bpm=['SARUN05-DBPM070:X1','SARUN05-DBPM070:Y1']
myscan.run(bpm,100)


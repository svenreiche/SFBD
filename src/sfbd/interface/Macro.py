import json


class Macro:
    """
    routine to parse a json file describint measurements
    """
    def __init__(self):
        self.sensor = []
        self.plot = []
        self.preaction={}
        self.actuator={}
        self.path = '/sf/data/applications/BD-pyREALTA/macro'
        self.filename = None
        self.type = 'Time Recording'
        self.nsample = 1000
        self.nstep = 1
        self.settle = 0.
        self.timeout = 10.
        self.name = 'Generic'
        self.snap = 'default'
        self.postprocessor = 'None'
        self.EpicsSensor = False
        self.new()

    def new(self):
        self.sensor.clear()
        self.preaction.clear()
        self.plot.clear()
        self.actuator.clear()
        self.type='Time Recording'
        self.nsample = 1000
        self.nstep = 1
        self.settle = 0.
        self.timeout = 10.
        self.name = 'Generic'
        self.snap = 'default'
        self.postprocessor = 'None'
        self.EpicsSensor = False
        self.filename = None

    def save(self,filename):
        self.filename=filename
        macro={}
        macro['Name'] = self.name
        macro['Type'] = self.type
        macro['Sample'] = self.nsample
        macro['Steps'] = self.nstep
        macro['Epics'] = self.EpicsSensor 
        macro['Sensor'] = self.sensor
        macro['Actuator'] = self.actuator
        macro['Snapfile'] = self.snap
        macro['Plot'] = self.plot
        macro['Settletime'] = self.settle
        macro['Timeout'] = self.timeout
        macro['PostProcessor'] = self.postprocessor
        macro['Preaction'] = self.preaction
        with open(filename, 'w') as outfile:
            json.dump(macro, outfile,indent=4)

    def load(self,filename):
        self.new()
        self.filename = filename
        with open(filename) as f:
            macro=json.load(f)
            self.name=macro['Name']
            self.type=macro['Type']
            if 'Actuator' in macro.keys():
                self.actuator = macro['Actuator']
            self.nsample=macro['Sample']
            if 'Steps' in macro.keys():
                self.nstep = macro['Steps']
            self.sensor=macro['Sensor']
            if 'Settletime' in macro.keys():
                self.settle = macro['Settletime']
            if 'Timeout' in macro.keys():
                self.timeout = macro['Timeout']
            if 'Snapfile' in macro.keys():
                self.snap=macro['Snapfile']
            if 'Plot' in macro.keys():
                self.plot = macro['Plot']
            else:
                self.plot.clear()
            if 'PostProcessor' in macro.keys():
                self.postprocessor = macro['PostProcessor']
            if 'Preaction' in macro.keys():
                self.preaction = macro['Preaction']
            else:
                self.preaction.clear()
            if 'Epics' in macro.keys():
                self.EpicsSensor = macro['Epics']
        

#
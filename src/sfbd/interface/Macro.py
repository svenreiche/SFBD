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
        self.path = '/sf/data/applications/BD-MacroManager/macros'
        self.filename = None
        self.type = 'Time Recording'
        self.nsample = 1000
        self.nstep = 1
        self.settle = 0.
        self.timeout = 10.
        self.name = 'Generic'
        self.snap = 'default'
        self.postprocessor = 'None'
        self.EpicsSensor = []
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
        self.EpicsSensor.clear()
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
                for key in self.actuator:
                    if not 'Relative' in self.actuator[key].keys():
                        self.actuator[key]['Relative']=False
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


#-----------------------------------
# manipulating elements in the macro
    def addActuators(self,channels):
        for channel in channels:
            if not channel in self.actuator.keys():
                self.actuator[channel]={'Start':0,'End':0,'Readback':'','Tolerance':0,'Relative':False}

    def updateActuators(self,channel,val1,val2,val3,val4,val5):
        if channel in self.actuator.keys():
            self.actuator[channel] = {'Start':val1,'End':val2,'Readback':val3,'Tolerance':val4,'Relative':val5}

    def removeActuators(self,channel):
        if channel in self.actuator.keys():
            del self.actuator[channel]
        
    def addPreaction(self,channels):
        for channel in channels:
            if not channel in self.preaction.keys():
                self.preaction[channel]=0.

    def removePreaction(self,channel):
        if channel in self.preaction.keys():
            del self.preaction[channel]

    def updatePreaction(self,channel,val):
        if channel in self.preaction.keys():
            self.preaction[channel] = val

    def addBSChannels(self,channels):
        for channel in channels:
            if not channel in self.sensor:
                self.sensor.append(channel)

    def removeBSChannels(self,channels):
        for channel in channels:
            if channel in self.sensor:
                self.sensor.remove(channel)

    def addEPICSChannels(self,channels):
        for channel in channels:
            if not channel in self.EpicsSensor:
                self.EpicsSensor.append(channel)

    def removeEPICSChannels(self,channels):
        for channel in channels:
            if channel in self.EpicsSensor:
                self.EpicsSensor.remove(channel)

    def addLivePlot(self,channels):
        for channel in channels:
            if not channel in self.plot:
                self.plot.append(channel)

    def removeLivePlot(self,channels):
        for channel in channels:
            if channel in self.plot:
                self.plot.remove(channel)

#

# SFBD
Basic python package for various task, in particular interfacing with the machine, for the swissfel beam  dynamics gorup.

# Structure

### SFBD.DAQ
Collectionof classes  to interface with the machine via EPICS, BSREAD etc.

##### SFBD.DAQ.PVAccess
Class to connect to a list of EPICS-PVs for writing to and reading from them

##### SFBD.DAQ.ScanBS
Class for running a scan, including connecting to the channels (both BSREAD and EPICS), allocating data, setting actuators. The progress is 
indicated with signals

##### SFBD.DAQ.ActuatorPV
Class to handle the setting of an actuator, using a thread


### SFBD.INTERFACE
Collection of classes or routines to interface with other services at SwissFEL

##### SFBD.INTERFACE.elog
Interface to the PSI ELOG

##### SFBD.INTERFACE.MACRO
Class to interface a measurment macro - a collection of channels for reading and writing

##### SFBD.INTERFACE.snapshot
Class to interface with the snapshot GUI, avoiding some inconsistencies and adding some functionality.

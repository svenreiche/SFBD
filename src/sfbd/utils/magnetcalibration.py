import numpy as np

# conversion curves for magnets

quad={}
bend={}
sext={}

magcal={}
# Sextupole [Order,PhysicalLength,MagneticLength,Imax,Ilin,b0,b1,b2,b3,R] # b1/R is gradient at Imax
magcal['HFA']  =[2, 0.08,  0.08,  10.0, 10.1, 0.0, 0.0182,  0,  0, 22e-3] 
magcal['HFB']  =[2, 0.08,  0.08,  10.0, 10.1, 0.0, 0.1445,  0,  0, 10e-3]         
    
# Quadrupole [PhysicalLength,MagneticLength,Imax,Ilin,b0,b1,b2,b3,R] # b1/R is gradient at Imax
magcal['QFA']  =[1, 0.15, 0.173, 150.0, 91.1, 0.0, 0.74521, -0.00813, -0.03542, 22.5e-3] 
magcal['QFB']  =[1, 0.08,  0.11,  10.0, 4.9,  0.0, 0.03815,   -1.8e-4,   -0.7e-3, 22.5e-3] 
magcal['QFC']  =[1, 0.08,  0.11,  10.0, 10.1, 0.0,     0.5,      0.0,      0.0,     1.0] 
magcal['QFD']  =[1, 0.15,  0.1628,10.0, 5.6,  0.0, 0.23313, -27.6e-4,  15.5e-4,   0.011] 
magcal['QFF']  =[1, 0.08, 0.0875, 10.0, 2.9,  0.0, 0.32897,  -0.5e-4,  -42.9e-4,   0.006] 
magcal['QFM']  =[1, 0.3,  0.311,   50.0, 21.1, 0.0,    0.64541,      -0.00296,      -0.00617,     0.011] 
magcal['QFCOR']=[1, 0.16, 0.11,   10.0, 10.1, 0.0,  0.0278,      0.0,      0.0,     1.0] 
magcal['QFU']  =[1, 0.04, 0.04,      0,    0,   6,     0.0,      0.0,      0.0,     1.0] 
magcal['QFA-SKEW']=magcal['QFA']
magcal['QFB-SKEW']=magcal['QFB']
magcal['QFC-SKEW']=magcal['QFC']
magcal['QFD-SKEW']=magcal['QFD']
magcal['QFDM']=magcal['QFD']
magcal['QFCOR-SKEW']=magcal['QFCOR']

#Bends  [PhysicalLength,MagneticLength,Imax,Ilin,b0,b1,b2,b3] # b1 is the field strength [T] (linear term) at Imax
magcal['SHA']  =[0, 0.25,   0.235,  30.942, 31.042,  0.0,   0.052168,     0.0,     0.0] 
magcal['AFL']  =[0, 0.12,  0.1509,    50.0,   11.6,  0.0,    0.40606,  3.1e-4,-28.7e-4] 
magcal['AFBC1']=[0, 0.25,    0.27,   200.0,   45.2,  0.0,    0.46402,  4.5e-4,-24.7e-4] 
magcal['AFBC3']=[0,  0.5,  0.5295,   150.0,   56.7,  0.0,    0.97172, -7.3e-4,-38.2e-4] 
magcal['AFS']  =[0,  1.0,     1.0,   200.0,  200.1,  0.0,       0.96,     0.0,     0.0] 
magcal['AFSS'] =[0, 0.36,    0.36,   200.0,  200.1,  0.0,      0.281,     0.0,     0.0] 
magcal['AFD1'] =[0,  2.0,     2.0,   200.0,  200.1,  0.0,     1.6871,     0.0,     0.0] 
magcal['AFD2'] =[0,  1.1,     1.1,   150.0,  150.1,  0.0,      1.609,     0.0,     0.0] 
magcal['AFP1'] =[0,  0.3,     0.3,    50.0,   50.1,  0.0,        1.0,     0.0,     0.0]
magcal['AFP2'] =[0,  0.3,     0.3,    50.0,   50.1,  0.0,        1.0,     0.0,     0.0]
magcal['AFDL'] =[0,  1.0,   1.016  ,   135,   99.7,  0.0,    1.46701,-0.01159,-0.03781] # Where is the specification found? 1 T at 50 A is ASSUMED. 


def getK1L(name, mtype, I, Energy):

    if name in magcal.keys():
        cal=magcal[name]
    elif mtype in magcal.keys():
        cal=magcal[mtype]
    else:
        print('*** ERROR: Magnet:',name,'of Type',mtype,'not found')
        return 0

    # calculate Brho factor
#    Energy=Energy*1e-6  # Energy is in eV!!!!
    gamma=(Energy+0.511)/0.511 # Energy in units of MeV since 29.06.2015
    beta=np.sqrt(1-1/gamma**2)
    p=511e3*beta*gamma/1e9 # momentum in GeV/c
    brho=p/0.299792 # P[GeV/c]=0.3*Brho[T.m]

    R=1
    order = cal[0]
    if order < 1:   # dipole have no radius
        [order, PhysicalLength,MagneticLength,Imax,Ilin,b0,b1,b2,b3]=cal  # quick conversion for dipoles which have no reference radius
    else:
        [order, PhysicalLength,MagneticLength,Imax,Ilin,b0,b1,b2,b3,R]=cal  # quick conversion for quadrupoles and sextupoles

    if order > 0:
        R=R**order  # cross check needed. Is R^2 good for sextupole or must it be R^2/2 - apparrently it has to be R^2
    
    if abs(I)<Ilin:
        B = (b0 + b1*np.abs(I)/Imax)
    else:
        B = (b0 + b1*np.abs(I)/Imax + b2*((abs(I)-Ilin)**2/(Imax-Ilin)**2) + b3*((abs(I)-Ilin)**3/(Imax-Ilin)**3))

    val=np.sign(I)*B/brho*MagneticLength/R
    if order < 1:
        val=val*180/np.pi    # for dipoles and correctors convert to angle in degree. Correctors have them calibrated back in the calling functions
    return val



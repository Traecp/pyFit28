#!/usr/bin/env python
######################################################################################################
# Converter for Spec file (Spec2IXS)
# Gael Goret and Alessandro Mirone and Bjorn Wehinger for the European Synchrotron Radiation Facility
# gael.goret@esrf.fr
######################################################################################################
import sys, traceback, string, os, h5py
import numpy as np
from types import *
from PyMca5.PyMca import SpecFileDataSource as sfds


def interactive_extractor(fn):
    """
    allow to explore the values of differents attributs for different scans
    """
    sf = sfds.SpecFileDataSource(fn)
    info = sf.getSourceInfo()
    print '-----------------------------------------------------------------'
    print info['KeyList']
    print '-----------------------------------------------------------------'
    scan =raw_input('Enter a scan number \n')
    data = []
    try:
        data = sf.getDataObject(scan)
    except: 
        print 'error for scan : %s'%scan
        
    print data.getInfo()['LabelNames']
    label =raw_input('Enter an attribut label \n')
    labelid = data.getInfo()['LabelNames'].index(label)
    for mesure in data.data:
        print mesure[labelid] 


def read_configuration_file(cfgfn):
    """
    cfgfn is the filename of the configuration file.
    the function return an object containing information from configuration file (cf inside cfg file).
    """
    if True  :
        try:
            s=open(cfgfn,"r")
        except:
            print " Error reading configuration file " ,  cfgfn			
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            print "*** print_exception:"
            traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback,
                                      limit=None, file=sys.stdout)
            raise Exception
        class config():
            exec(s)
        cfg = config()
        
        allowed_keys={"scan_types":ListType, "ref":StringType, "deta_num":DictType, "deta":DictType,"mhkl":DictType, "deltaa":FloatType, "tcorr":DictType}
        
        for key in allowed_keys.keys() :
            if key not in dir(cfg):
                raise  Exception , ("Key not found in config file : %s"%key)
        for key in dir(cfg):
            if key not in allowed_keys.keys():
                if key[0] != "_":
                    raise  Exception , ("Config file has spurious key %s"%key)
            else :
                if not (type(getattr(cfg,key)) is allowed_keys[key]):
                    raise  Exception , ("Wrong type for key %s in config file"%key)
        return cfg

def get_deta(data,cfg,zeroid):
    """
    Extract deta intensity values
    """	
    Deta = {}
    for d in cfg.deta.keys():
        if d != cfg.ref:
            detaid = data.getInfo()['LabelNames'].index(d)
            deta = np.array(data.data[:,detaid])
            for z in zeroid:
                deta = np.delete(deta,z)
            Deta[d]	= deta
    return Deta


def T2DT(T,cfg):
    """
    T is a dictionary (dict) which contain label of detector and sequence of temperature.
    Tcoor is a dictionary (dict) which contain label of detector and temperature correction.
    ref is a label (string) defining the monochromator in T and Tcoor dictionnary.
    T2DT compute deltaT for all detectors (Tn-To-Tcoor)
    """
    DT = {}
    for d in T.keys():
        if d != cfg.ref:
            DT[d] = [float(T[d][x]-T[cfg.ref][x]-cfg.tcorr[d]) for x in range(min(len(T[d]),len(T[cfg.ref])))]
    return DT


def D2MHKL(motang,cfg):
    """
    motang (deg) is the angle of the monocromator.
    cfg.mhkl is the conversion table from degree to mhkl value.
    deltaa is the incertitude about the monochromator angle.
    """
    for a in cfg.mhkl.keys():
        if  a - cfg.deltaa <= motang and motang <= a + cfg.deltaa:
            return cfg.mhkl[a]
    print 'Warning: convertion from monochromator angle (%f) to hkl failed'%motang
    mhkl =  raw_input('Enter a value for monochromator hkl :\n')
    return string.atoi(mhkl)
    
def R2T(R):
    """
    Resistances to Temperatures.
    R is a sequence of resistances.
    """
    c = 0.001130065
    g = 0.0002405245
    e = 0.0000001089848
    f = -266.5
    def T(a):
        return 1./(c+(g*np.log(a)+e*np.log(a)**3))
    return [T(a) for a in R]	


def T2E(Temp,mhkl):
    """
    Temperatures to Energie.
    Temp is a sequence of Temperatures.
    mhkl is supposed to be an integer.
    """
    ASI = 5.43102088
    HBARC = 12398.483903
    factor = 1000*HBARC/(2*ASI/np.sqrt(3.)*np.sin(np.pi/2.))
    def E(T):
        return (T*(2.581e-6+T*0.008e-6)*factor*mhkl)
    return [E(T) for T in Temp]


def R2DE(data,cfg,mhkl,zeroid):
    """
    Convert a sequence of resistance extracted from data into the delta of energy -> cf R2T(),T2DT(),T2E()
    data is a SpecFileDataObject from the SpecFileDataSource module of PyMca.
    cfg is a dictionary containing all the configuration information -> cf read_configuration_file().
    mhkl is supposed to be an integer.
    """
    R={}
    for d in cfg.deta.keys():
        premid = [data.getInfo()['LabelNames'].index(cfg.deta[d])]
        r = np.array(data.data[:,premid])
        for z in zeroid:
            r = np.delete(r,z)
        R[d] = r
            
    T = {}
    for d in R.keys():
        T[d] = R2T(R[d]) 
        
    DT = T2DT(T,cfg)
    
    DE = {}
    for d in DT.keys():
        DE[d] = T2E(DT[d],mhkl)
        
    return DE


def norma_error_calc(Deta,ione):
    """
    compute the normalized intensity, the normalized error and the error
    Deta is the intensity extacted from the SpecFileDataObject
    ione is the monitor incoming intensity
    """
    # mean_ione = np.mean(ione)
    facts_norm= 1.0/ione
    Err = {}
    NErr = {}
    NI = {}
    for d in Deta.keys():
        Err[d]  =  np.sqrt(Deta[d])
        NErr[d] =  Err[d]*facts_norm
        NI[d]   =  Deta[d]*facts_norm
    return NI,NErr,Err


def save_data_as_hdf5(fn,dscan,cfg):
    hdf = h5py.File(fn+'.h5','w')
    for s in dscan.keys():
        scangrp = hdf.create_group(str(s))
        for d in cfg.deta.keys():
            if d != cfg.ref:
                detagrp = scangrp.create_group(str(cfg.deta_num[d]))
                for q in dscan[s].keys():
                    if type(dscan[s][q]) is DictType:
                        length = len(dscan[s][q][d])
                        qn = detagrp.create_dataset(q, (length,),'f')
                        qn[:] = dscan[s][q][d]
                    elif type(dscan[s][q]) is np.ndarray:
                        length = len(dscan[s][q])
                        qn = detagrp.create_dataset(q, (length,),'f')
                        qn[:] = dscan[s][q]
                    else:
                        print 'Warning: strange type of key in dscan :%s'%type(dscan[s][q])
    hdf.close()

if __name__ == '__main__':
    pass
    
    

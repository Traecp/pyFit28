#!/usr/bin/env python
######################################################################################################
# GUI for inelastic spectra fitting 
# Thanh-Tra NGUYEN for the European Synchrotron Radiation Facility
# thanhtra0104@gmail.com
######################################################################################################
import sys, os, traceback
import numpy as np
from types import *
from lmfit import Parameters, minimize, report_fit, Minimizer
from lmfit.lineshapes import lorentzian, gaussian
from scipy import constants, signal
from matplotlib.pylab import *
"""
gaussian(x,A,x0,sigma), fwhm = sigma * 2 * sqrt(2ln2)
lorentzian(x,A,x0,sigma), fwhm = 2*sigma
"""
kB = constants.k/constants.eV #Boltzmann constant in eV/K

def sup_pow_2(x):
    p=1
    while(p<x):
        p=p*2
    return p
    
def conv(data, res):
    return signal.convolve(data, res, mode="same", method="fft")/res.sum()
    
def avg_step(x):
    N = x.size
    avstep = (x[-1]-x[0])/(N-1)
    return avstep
    
def pseudoVoigt_resolution(x,mu,wG,wL):
    """pseudo-voigt used as resolution function - area normalized to 1"""
    sigG = wG/np.sqrt(8.*np.log(2.))
    sigL = wL/2.
    r = mu * lorentzian(x, 1., 0., sigL) + (1-mu) * gaussian(x, 1.0, 0.0, sigG)
    fac = r.sum()*(x[-1]-x[0])/(x.size - 1)
    r = r/fac
    return r 
    
def ELASTIC(x, A, x0, G):
    G = G/2.
    l28 = A*G/np.pi/((x-x0)**2 + G**2)
    return np.nan_to_num(l28)
    
def LOR(x, A, x0, G, KT):
    G = G/2.
    b = x/(1. - np.exp(-1.*x/KT))
    b[x.size/2]=1.
    l28 = A*G*G/4/np.pi* b * (1./((x-x0)**2 + G**2) + 1./((x+x0)**2 + G**2))
    return np.nan_to_num(l28)
    
def DHO(x, A, x0, G, KT):
    b = x/(1. - np.exp(-1.*x/KT))
    b[x.size/2]=1.
    d = A*G*x0*b/ ((x0**2 - x**2)**2 + G**2 * x**2)
    return np.nan_to_num(d)
     
def read_resolution_file(cfgfn,allowed_keys={} ):
    """
    cfgfn is the filename of the configuration file.
    the function return an object containing information from configuration file (cf inside cfg file).
    """
    
    try:
        s=open(cfgfn,"r")
    except:
        print " Error reading configuration file " ,  cfgfn
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        print "*** print_exception:"
        traceback.print_exception(exceptionType, exceptionValue, exceptionTraceback,
                              limit=None, file=sys.stdout)
        raise Exception
    class Config():
        exec(s)
    cfg = Config()    
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

    for key in cfg.res_param.keys():
        params = cfg.res_param[key]
        if(len(params)==3): params.append(0.0)
        
    return cfg
    
class Resolution_function:
    def __init__(self, deta):
        self.resolution_step = 0.1
        emin=-50
        emax=50
        npts = int((emax-emin)/self.resolution_step)
        npts = sup_pow_2(npts) +1
        nc = npts//2
        x = np.arange(npts)
        self.x_res = (x-nc)*self.resolution_step
        if deta==None:
            deta = [0.5,1.0,1.0]#doesn't matter, because we are not going to convolute with it.
        self.resolution = pseudoVoigt_resolution(self.x_res, deta[0], deta[1], deta[2])
        
class Spectrum_model:
    def __init__(self, pars, energy, lineshape, convolution=1, deta=None, interpolation=1):
        # pars = Parameters["noise", "el_A", "el_x0", "el_w", "T", "phonon_A_0", "phonon_E_0", "phonon_G_0", "phonon_A_n", ...]
        # spectrum model = elastic part + (phonons_part)n
        self.number_of_phonon = 0
        self.energy = energy
        self.pars = pars
        self.RES = Resolution_function(deta)
        self.resolution = self.RES.resolution
        
        self.extent_energy = self.RES.x_res.max() - self.RES.x_res.min() + self.energy.max() - self.energy.min()
        # self.extent_energy = 2.0*np.max(abs(self.RES.x_res)) + 2*np.max(abs(self.energy))
        self.energy_step = self.RES.resolution_step
        npts = int(self.extent_energy/self.energy_step)
        self.npts = sup_pow_2(npts) +1
        nc = self.npts//2
        x = np.arange(self.npts)
        self.interpolated_energy = (x-nc)*self.energy_step
        
        
        self.lineshape = lineshape
        self.interpolation = interpolation
        self.convolution = convolution
        
        self.get_model()
        
    def get_model(self):
        pars = self.pars
        x = self.interpolated_energy
        noise = pars["BG"].value
        el_A = pars["el_A"].value
        el_x0  = pars["el_x0"].value
        el_w   = pars["el_w"].value
        T           = pars["T"].value
        KT = T*kB*1000
        model = ELASTIC(x, el_A, el_x0, el_w)
        self.elastic_line = ELASTIC(x, el_A, el_x0, el_w)
        inelastic_lines = []
        vars_number = len(pars.keys()) - 5 #Temperature should be the same for every phonon peak, each phonon peak has therefore 3 variables: A, E, Gamma
        self.number_of_phonon = vars_number/3
        x = x - el_x0
        for i in xrange(self.number_of_phonon):
            A = pars["phonon_A_%d"%i].value
            E = pars["phonon_E_%d"%i].value
            G = pars["phonon_G_%d"%i].value
            if self.lineshape=="lor":
                inelastic_line = LOR(x,A,E,G,KT)
            elif self.lineshape=="dho":
                inelastic_line = DHO(x,A,E,G,KT)
            model += inelastic_line
            inelastic_lines.append(inelastic_line)
        model = model + noise
        if self.convolution:
            convoluted_model  = signal.convolve(model, self.resolution, mode="same", method="fft")/self.resolution.sum()
            self.elastic_line = signal.convolve(self.elastic_line, self.resolution, mode="same", method="fft")/self.resolution.sum()
            for i in xrange(self.number_of_phonon):
                inelastic_lines[i] = signal.convolve(inelastic_lines[i], self.resolution, mode="same", method="fft")/self.resolution.sum()
        else:
            convoluted_model = model
        if self.interpolation:
            self.total_model = np.interp(self.energy, self.interpolated_energy, convoluted_model)
            self.elastic_line = np.interp(self.energy, self.interpolated_energy, self.elastic_line)
            self.inelastic_lines = []
            for i in xrange(self.number_of_phonon):
                inel = np.interp(self.energy, self.interpolated_energy, inelastic_lines[i])
                self.inelastic_lines.append(inel)
        else:
            self.total_model = convoluted_model
            self.inelastic_lines = inelastic_lines
            self.energy = self.interpolated_energy
        self.total_model = np.nan_to_num(self.total_model)
            
class Fit:
    def __init__(self, pars_init, datafile, shape, convolution=1, deta = None):
        self.convolution = convolution
        self.datafile = datafile
        self.shape = shape
        self.deta = deta
        self.data = np.loadtxt(self.datafile)
        self.energy = self.data[:,0]
        self.intensity = self.data[:,1]
        self.intensity_err = self.data[:,2]
        self.pars_init = pars_init
        M = Minimizer(chisquared, self.pars_init, fcn_args=(self.energy, self.intensity, self.intensity_err, self.shape, self.convolution, self.deta),nan_policy="omit")
        result0 = M.minimize(method='Nelder-Mead', options={'maxfev':200})#, options={'maxfev':200}
        self.result = M.minimize(params=result0.params)#, maxfev=1000
        
        self.num_excitation = (len(self.pars_init.keys())-5)/3
        self.write_result()
        
    def write_result(self):
        outfile_par = os.path.splitext(self.datafile)[0]+".par"
        outfile_fit = os.path.splitext(self.datafile)[0]+".fit"
        txt  = "Results are deconvoluted with the resolution function\n"
        txt += "--------------------------------------------------------\n"
        txt += "Model: %s\n"%self.shape.upper()
        txt += "N# function evaluations: %d\n"%self.result.nfev
        txt += "Reduced chi-square: %5.2f \n"%self.result.redchi
        txt += "Temperature : %05.2f +/- %05.2f \n"%(self.result.params["T"].value, self.result.params["T"].stderr)
        txt += "--------------------------------------------------------\n"
        txt += "Elastic line: \n"
        txt += "Amplitude = %05.4f +/- %05.4f \n"%(self.result.params["el_A"].value, self.result.params["el_A"].stderr)
        txt += "Center    = %05.4f +/- %05.4f \n"%(self.result.params["el_x0"].value, self.result.params["el_x0"].stderr)
        txt += "Width     = %05.4f +/- %05.4f \n"%(self.result.params["el_w"].value, self.result.params["el_w"].stderr)
        for i in xrange(self.num_excitation):
            txt += "--------------------------------------------------------\n"
            txt += "Inelastic line %d: \n"%(i+1)
            txt += "Amplitude = %05.4f +/- %05.4f \n"%(self.result.params["phonon_A_%d"%i].value, self.result.params["phonon_A_%d"%i].stderr)
            txt += "Center    = %05.4f +/- %05.4f (Relative to the elastic line)\n"%(abs(self.result.params["phonon_E_%d"%i].value), self.result.params["phonon_E_%d"%i].stderr)
            txt += "Width     = %05.4f +/- %05.4f \n"%(self.result.params["phonon_G_%d"%i].value, self.result.params["phonon_G_%d"%i].stderr)
            
        f = open(outfile_par, "w")
        f.write(txt)
        f.close()
        self.result_text = txt
        # Write the fitting data 
        header = "Energy \t Intensity \t Intensity_errorbar \t Total_model \t Elastic_line"
        outArray = np.vstack([self.energy, self.intensity,self.intensity_err])
        mod = Spectrum_model(self.result.params, self.energy, self.shape, convolution=self.convolution, deta=self.deta, interpolation=1)
        outArray = np.vstack([outArray, mod.total_model, mod.elastic_line])
        for i in xrange(self.num_excitation):
            outArray = np.vstack([outArray, mod.inelastic_lines[i]])
            header += "\t Inelastic_line_%d"%(i+1)
        outArr = outArray.transpose()
        np.savetxt(outfile_fit, outArr, fmt="%10.4f", header = str(header))
        
    
  
def chisquared(pars,x,y,err, lineshape, convolution, deta):
    Mod = Spectrum_model(pars, x, lineshape, convolution=convolution, deta=deta, interpolation=1)
    model = Mod.total_model
    return (y-model)/err
    

def get_ana_number(datafile):
    fn = os.path.basename(datafile)
    fn = os.path.splitext(fn)[0]
    fn = fn.split("_")[-1]
    n = len(fn)
    if n==1:
        ana = int(fn)
    elif n==2:
        ana = int(fn[-1])
    else:
        ana = None
    return ana
    
if __name__=="__main__":
    pass
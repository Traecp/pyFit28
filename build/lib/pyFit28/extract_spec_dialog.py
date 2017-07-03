#!/usr/bin/python
# -*- coding: utf-8 -*-
######################################################################################################
# GUI for inelastic spectra fitting 
# Thanh-Tra NGUYEN for the European Synchrotron Radiation Facility - ID28
# thanhtra0104@gmail.com
######################################################################################################
import numpy as np
import sys, os
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QDialog
from pyFit28.extract import *
from PyQt4.QtCore import QThread, SIGNAL
from pyFit28.ui.extract_spec import Ui_Extract_Spec

class ExtractionThread(QThread):
    def __init__(self, specfile, config_file):
        QThread.__init__(self)
        self.specfile = specfile
        self.config_filename = config_file
    def __del__(self):
        self.wait()
    def run(self):
        cfgfn = self.config_filename
        fn    = self.specfile
        cfg = read_configuration_file(cfgfn)
        sf = sfds.SpecFileDataSource(fn)
        info = sf.getSourceInfo()
        scans = info['KeyList']
        alldata = []
        # print '-----------------------------------------------------------------'
        for scan in scans:
            try:
                s = sf.getDataObject(scan)
                scan_type = s.info['Command'].split()[1]
                if scan_type in cfg.scan_types:
                    alldata += [sf.getDataObject(scan)]
            except:
                txt = 'Warning: cannot read scan number %s, data type problem or scan aborted.'%scan[:-2]
                self.emit(SIGNAL("warning"), txt)
        # print '-----------------------------------------------------------------'
        dscan={}
        total_item=len(alldata)
        nb_item_done = 0
        for data in alldata:
            motid = data.getInfo()['MotorNames'].index('Mono')
            motang =  data.getInfo()['MotorValues'][motid]
        
            ioneid = data.getInfo()['LabelNames'].index('ione')
            ione = np.array(data.data[:,ioneid])
            
            zeroid=[]
            if 0 in ione:
                zeroid = np.where(ione==0)
                for z in zeroid:
                    ione = np.delete(ione,z)
                txt= 'Warning: data points with incoming intensity ione == 0 from scan number %d removed'%data.info['Number']
                self.emit(SIGNAL("warning"), txt)
                    
            Deta = get_deta(data,cfg,zeroid)
            
            NI,NErr,Err = norma_error_calc(Deta,ione)
            mhkl = D2MHKL(motang,cfg)
            DE = R2DE(data,cfg,mhkl,zeroid)
            dirfn = fn + '_extract'
            if not os.path.exists(dirfn):
                os.mkdir(dirfn)
            
            dscan[data.info['Number']]={'DE':DE,'NI':NI,'NErr':NErr,'Deta':Deta,'ione':ione,'Err':Err}
            
            for d in DE.keys():
                outfile = os.path.basename(fn) + '_%d_A%d.dat'%(data.info['Number'],cfg.deta_num[d])
                outfile = os.path.join(dirfn, outfile)
                output = open(outfile,'w')
                for i in range(len(DE[d])):
                    output.write('%.3f %.2f %.2f 1 %d %d %.2f\n'%(DE[d][i],NI[d][i],NErr[d][i],Deta[d][i],ione[i],Err[d][i]))
                output.close()
            nb_item_done += 1
            frac = nb_item_done/total_item*100
            self.emit(SIGNAL("partial_done"), frac)
        save_data_as_hdf5(fn,dscan,cfg)
        self.emit(SIGNAL("hdf5_written"))
        
class Extract_spec_Dialog(QDialog, Ui_Extract_Spec):
    def __init__(self):
        super(Extract_spec_Dialog, self).__init__()
        self.setupUi(self)
        self.progressBar.hide()
        self.label_Done.setText("")
        self.label_Done.hide()
        self.spec_btn.clicked.connect(self.find_spec)
        self.config_btn.clicked.connect(self.find_config)
        self.extract_btn.clicked.connect(self.start_extraction)
        self.current_folder = os.getcwd()
        self.has_spec = False
        self.has_config = False
        
    def closeEvent(self, event):
        event.accept()
        
    def find_spec(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, "Browse the SPEC file to extract", self.current_folder)
        self.specfile = str(fn)
        self.spec_field.setText(self.specfile)
        self.current_folder = os.path.dirname(self.specfile)
        if fn:
            self.has_spec = True
    
    def find_config(self):
        fn = QtGui.QFileDialog.getOpenFileName(self, "Browse the configuration file", self.current_folder)
        self.config_filename = str(fn)
        self.config_field.setText(self.config_filename)
        if fn:
            self.has_config = True
        
    def start_extraction(self):
        if self.has_spec and self.has_config:
            self.progressBar.show()
            self.label_Done.setText("<html><head/><body><p><span style=' font-size:12pt; color:#ff0000;'>Extracting and writing ASCII files</span></p></body></html>")
            self.label_Done.show()
            self.EXT = ExtractionThread(self.specfile, self.config_filename)
            self.connect(self.EXT, SIGNAL("warning"), self.warning)
            self.connect(self.EXT, SIGNAL("partial_done"), self.partial_done)
            self.connect(self.EXT, SIGNAL("hdf5_written"), self.done)
            self.EXT.start()
        else:
            self.messageBox = QtGui.QMessageBox()
            self.messageBox.setIcon(QtGui.QMessageBox.Critical)
            self.messageBox.setText("You didn't select the Spec file AND the configuration file. Please do it before extracting.")
            self.messageBox.setWindowTitle("Warning - Files missing ...")
            self.messageBox.show()
        
        
    @QtCore.pyqtSlot()
    def partial_done(self, frac):
        self.progressBar.setValue(frac)
        
    @QtCore.pyqtSlot()
    def warning(self, txt):
        self.label_Done.setText("<html><head/><body><p><span style=' font-size:12pt; color:#ff0000;'>%s</span></p></body></html>"%txt)
        
    @QtCore.pyqtSlot()
    def done(self):
        self.label_Done.setText("<html><head/><body><p><span style=' font-size:12pt; color:#ff0000;'>HDF5 file written. Normal end.</span></p></body></html>")
        
        
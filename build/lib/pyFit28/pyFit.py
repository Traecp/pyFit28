#!/usr/bin/python
# -*- coding: utf-8 -*-
######################################################################################################
# GUI for inelastic spectra fitting 
# Thanh-Tra NGUYEN for the European Synchrotron Radiation Facility - ID28
# thanhtra0104@gmail.com
######################################################################################################
import numpy as np
import sys, os, time
from types import DictType, FloatType
from os import listdir
from os.path import isfile,join
from matplotlib.ticker import FormatStrFormatter
from matplotlib import rcParams
from matplotlib.figure import Figure
from pyFit28.functions_models import *
from pyFit28.ExcitationRow import ExcitationRow
from lmfit import Parameters
from pyFit28.extract_spec_dialog import Extract_spec_Dialog

rcParams['font.size'] = 14
rcParams['axes.labelsize'] = 'medium'
rcParams['legend.fancybox'] = True
rcParams['legend.handletextpad'] = 0.5
rcParams['legend.fontsize'] = 'medium'
rcParams['figure.subplot.bottom'] = 0.13
rcParams['figure.subplot.top'] = 0.93
rcParams['figure.subplot.left'] = 0.14
rcParams['figure.subplot.right'] = 0.915
rcParams['grid.linestyle'] = ":"
rcParams['image.cmap'] = 'jet'
rcParams['savefig.dpi'] = 300

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QDialog, QMainWindow
from PyQt4.QtCore import QThread, SIGNAL
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
#********** GUI ***************************************************
from pyFit28.ui.example_config import Ui_Example_Config
from pyFit28.ui.example_resolution import Ui_Example_Resolution
from pyFit28.ui.help_dialog import Ui_Help_Dialog
from pyFit28.ui.mainWindow import Ui_MainWindow
#********** GUI ***************************************************
__version__ = "2017.7.13"
try:

    _fromUtf8 = QtCore.QString.fromUtf8

except AttributeError:

    def _fromUtf8(s):

        return s

class Example_Config(QDialog, Ui_Example_Config):
    def __init__(self):
        super(Example_Config, self).__init__()
        self.setupUi(self)
        
class Example_Resolution(QDialog, Ui_Example_Resolution):
    def __init__(self):
        super(Example_Resolution, self).__init__()
        self.setupUi(self)
        
class Help_Dialog(QDialog, Ui_Help_Dialog):
    def __init__(self):
        super(Help_Dialog, self).__init__()
        self.setupUi(self)
        self.example_resolution.clicked.connect(self.open_example_resolution)
        self.example_config.clicked.connect(self.open_example_config)
        
    def open_example_config(self):
        self.oec = Example_Config()
        self.oec.show()
        
    def open_example_resolution(self):
        self.oer = Example_Resolution()
        self.oer.show()
        
class MyQFileSystemModel(QtGui.QFileSystemModel):
    def setHeader(self, header):
        self.header_label = header
        
    def headerData(self, section, orientation, role):
        if not hasattr(self,"header_label"):
            self.header_label = "Name"
        if section == 0 and role == QtCore.Qt.DisplayRole:
            return self.header_label
        else:
            return super(QtGui.QFileSystemModel, self).headerData(section, orientation, role)


class FittingThread(QThread):
    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.use_convolution = self.parent.deconvolution_btn.isChecked()
    def __del__(self):
        self.wait()
    def run(self):
        if self.use_convolution:
            if self.parent.resolutionLoaded:
                goAhead=True
                convolution = 1
            else:
                goAhead=False
                self.emit(SIGNAL("resolution_missing"))
        else:
            goAhead=True
            convolution = 0
        if goAhead:
            lineshape = self.parent.lineShapeBox.currentText()
            if lineshape=="DHO":
                self.lineshape = "dho"
            elif lineshape=="Lorentzian":
                self.lineshape = "lor"
            if convolution:
                self.deta = self.parent.resolutionParams.res_param[self.parent.analyser]
            else:
                self.deta=None
            self.fitObject = Fit(self.parent.pars_init, self.parent.datafile, self.lineshape, convolution=convolution, deta=self.deta)
            self.emit(SIGNAL("fitting_done"), self.fitObject)
            
        
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)

        self.setWindowTitle("IXS spectra fitting program for ID28. Version %s"%__version__)
        # ****************** Toolbar actions settings ***********************************
        self.actionOpen.triggered.connect(self.loadData)
        self.actionExtract.triggered.connect(self.extractSpec)
        self.actionResolution.triggered.connect(self.loadResolution)
        self.actionHelp.triggered.connect(self.help)
        self.actionQuit.triggered.connect(self.close)#close is a method within QWidget
        self.treeView.doubleClicked.connect(self.itemChanged)
        self.fitButton.clicked.connect(self.fitting)
        self.scale_btn.clicked.connect(self.change_scale)
        self.loading_icon = QtGui.QMovie(_fromUtf8(":/loading"))
        self.loading_icon.setScaledSize(QtCore.QSize(25,25))
        self.fit_Label.setMovie(self.loading_icon)
        self.loading_icon.start()
        self.fit_Label.hide()
        # *********************** Model for Tree View *************************************
        # self.model = QtGui.QFileSystemModel()
        self.model = MyQFileSystemModel()
        self.filters = ["*.txt", "*.dat"]
        self.model.setNameFilters(self.filters)
        self.model.setNameFilterDisables(False)
        # *********************** VARIABLES *********************************************
        self.current_folder = os.getcwd()
        self.resolutionLoaded = False
        self.markers = []
        self.exRowNum = 0
        self.exListRow = []
        self.peak_x = []
        self.peak_y = []
        self.elastic_selected = False
        self.scale_changed = False
        self.use_convolution = self.deconvolution_btn.isChecked()
        #************************* PLOT ****************************************
        self.fig=Figure(dpi=100)
        self.ax  = self.fig.add_subplot(111)
        self.MAIN_XLABEL = r"$Energy\ transfer\ (meV)$"
        self.MAIN_YLABEL = r"$Normalized\ intensity\ (arb. unit)$"
        self.fig.subplots_adjust(left=0.15, right = 0.95, bottom=0.15, top=0.92)
        self.ax.set_xlabel(self.MAIN_XLABEL, fontsize=15)
        self.ax.set_ylabel(self.MAIN_YLABEL, fontsize=15)
        
        self.ax.grid(True)
        
        self.canvas  = FigureCanvas(self.fig)
        self.canvas.mpl_connect("button_press_event",self.on_press)
        self.figure_navigation_toolbar = NavigationToolbar(self.canvas, self.plotWin, coordinates=True)
        self.plotLayout.addWidget(self.figure_navigation_toolbar)
        self.plotLayout.addWidget(self.canvas)
        
        
    def change_scale(self):
        self.scale_changed = not(self.scale_changed)
        if self.scale_changed:
            self.scale_btn.setText("Linear scale")
            self.ax.set_yscale("log")
        else:
            self.scale_btn.setText("Log scale")
            self.ax.set_yscale("linear")
        self.canvas.draw()
        
    def closeEvent(self, event):
        # When user clicks on the Quit button on the toolbar or the red X button of the window
        event.accept()
        
    def init_plot(self):
        nbrows=len(self.exListRow)
        if nbrows>0:
            for i in xrange(nbrows):
                self.exListRow[-1].destroyRow()
        self.fitParamsDisplay.clear()
        self.ax.clear()
        self.ax.set_xlabel(self.MAIN_XLABEL, fontsize=15)
        self.ax.set_ylabel(self.MAIN_YLABEL, fontsize=15)
        self.ax.grid(True)
        self.exListRow = []
        self.exRowNum = 0
        self.markers = []
        self.peak_x = []
        self.peak_y = []
        self.elastic_selected = False
        
    def addExcitationRow(self):
        self.exRowNum += 1
        oneRow = ExcitationRow(self.exRowNum, self)
        self.formLayout.addWidget(oneRow)
        self.exListRow.append(oneRow)
        
    def on_press(self, event):
        
        if (event.inaxes == self.ax) and (event.button==3):
            self.x0 = event.xdata
            self.y0 = event.ydata
            please_insert = False
            if len(self.peak_x)>=0 and self.elastic_selected==False:
                # This is the elastic line 
                if len(self.peak_x)==0:
                    self.peak_x.append(self.x0)
                    self.peak_y.append(self.y0)
                    please_insert = False
                else:
                    self.peak_x.insert(0, self.x0)
                    self.peak_y.insert(0, self.y0)
                    please_insert = True
                    
                self.EL_amp_current.setText("%.1e"%self.y0)
                # self.EL_amp_min.setText("%.1e"%(self.y0*0.1))
                # self.EL_amp_max.setText("%.1e"%(self.y0*2))
                self.EL_cen_current.setText("%.2f"%self.x0)
                # self.EL_cen_min.setText("%.2f"%(self.x0*0.5))
                # self.EL_cen_max.setText("%.2f"%(self.x0*1.5))
                self.elastic_selected = True
                
            elif len(self.peak_x)>0 and self.elastic_selected:
                self.addExcitationRow()
                thisRow = self.exListRow[-1]
                thisRow.An_current.setText("%.2e"%self.y0)
                # thisRow.An_min.setText("%.2e"%(self.y0*0.1))
                # thisRow.An_max.setText("%.2e"%(self.y0*2))
                thisRow.Cn_current.setText("%.2f"%self.x0)
                # thisRow.Cn_min.setText("%.2f"%(self.x0*0.5))
                # thisRow.Cn_max.setText("%.2f"%(self.x0*1.5))
                self.peak_x.append(self.x0)
                self.peak_y.append(self.y0)
                please_insert = False
                
            pts, = self.ax.plot(self.x0, self.y0, color="r", marker="x", ms=20)
            marker_id = len(self.ax.lines)-1
            if please_insert:
                self.markers.insert(0, marker_id)
            else:
                self.markers.append(marker_id)
            self.canvas.draw()
            
        # To modify the elastic line: Delete elastic line with middle click
        elif (event.inaxes == self.ax) and (event.button==2):
            # self.markers[0].pop(0).remove()
            # self.markers[0].remove()
            self.ax.lines[self.markers[0]].remove()
            self.markers.remove(self.markers[0])
            self.peak_x.remove(self.peak_x[0])
            self.peak_y.remove(self.peak_y[0])
            self.canvas.draw()
            self.EL_amp_current.setText("")
            self.EL_cen_current.setText("")
            self.elastic_selected = False
            
    def loadData(self):
        folder = QtGui.QFileDialog.getExistingDirectory(self, "Select data folder", self.current_folder)
        # folder = os.path.dirname(folder)
        self.current_folder = str(folder)
        # print "Select ",folder
        self.model.setRootPath(folder)
        self.model.setReadOnly(True)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(folder))
        self.treeView.hideColumn(1)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)
        fn=os.path.basename(str(folder))
        self.model.setHeader(fn)
        self.model.setHeaderData(0, QtCore.Qt.Horizontal,fn)
        
    def itemChanged(self, signal):
        item = self.treeView.model().filePath(signal)
        if os.path.isfile(item):
            item = str(item)
            self.datafile = item
            self.data = np.loadtxt(item)
            self.energy = self.data[:,0]
            self.intensity = self.data[:,1]
            self.intensity_err = self.data[:,2]
            self.analyser = get_ana_number(item)
            self.init_plot()
            self.ax.errorbar(self.energy, self.intensity, yerr=self.intensity_err, fmt="ko-",label="Exp. Data")
            self.ax.set_yscale("linear")
            self.ax.legend(loc="best")
            datafile_basename = os.path.basename(self.datafile)
            self.ax.set_title("%s - Analyser #%d"%(datafile_basename, self.analyser))
            self.ax.set_xlim([self.energy.min(), self.energy.max()])
            self.canvas.draw()
            
    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            self.fitting()
            
    def init_params(self):
        self.pars_init = Parameters()
        #*********** Background **************************************************
        BG = self.BG_current.text()
        BG_min = self.BG_min.text()
        BG_max = self.BG_max.text()
        BG_fix = self.BG_fix.isChecked()
        BG_vary = not(BG_fix)
        BG = float(BG)
        BG_min = -np.inf  if BG_min=="" else float(BG_min)
        BG_max =  np.inf  if BG_max=="" else float(BG_max)
        self.pars_init.add("BG", value=BG, vary=BG_vary, min=BG_min, max=BG_max)
        #*********** Temperature **************************************************
        T = self.Temperature_current.text()
        T_min = self.Temperature_min.text()
        T_max = self.Temperature_max.text()
        T_fix = self.Temperature_fix.isChecked()
        T_vary= not(T_fix)
        T = float(T)
        T_min = -np.inf  if T_min=="" else float(T_min)
        T_max =  np.inf  if T_max=="" else float(T_max)
        self.pars_init.add("T", value=T, vary=T_vary, min=T_min, max=T_max)
        #*********** Elastic line *************************************************
        el_A     = self.EL_amp_current.text()
        el_A_min = self.EL_amp_min.text()
        el_A_max = self.EL_amp_max.text()
        el_A_fix = self.EL_amp_fix.isChecked()
        el_A_vary= not(el_A_fix)
        el_A     = float(el_A)
        el_A_min = -np.inf if el_A_min=="" else float(el_A_min)
        el_A_max =  np.inf if el_A_max=="" else float(el_A_max)
        self.pars_init.add("el_A", value=el_A, vary=el_A_vary, min=el_A_min, max=el_A_max)
        
        el_x0     = self.EL_cen_current.text()
        el_x0_min = self.EL_cen_min.text()
        el_x0_max = self.EL_cen_max.text()
        el_x0_fix = self.EL_cen_fix.isChecked()
        el_x0_vary= not(el_x0_fix)
        el_x0     = float(el_x0)
        el_x0_min = -np.inf if el_x0_min=="" else float(el_x0_min)
        el_x0_max =  np.inf if el_x0_max=="" else float(el_x0_max)
        self.pars_init.add("el_x0", value=el_x0, vary=el_x0_vary, min=el_x0_min, max=el_x0_max)
        
        el_w     = self.EL_width_current.text()
        el_w_min = self.EL_width_min.text()
        el_w_max = self.EL_width_max.text()
        el_w_fix = self.EL_width_fix.isChecked()
        el_w_vary= not(el_w_fix)
        el_w     = float(el_w)
        el_w_min = -np.inf if el_w_min == "" else float(el_w_min)
        el_w_max =  np.inf if el_w_max == "" else float(el_w_max)
        self.pars_init.add("el_w", value=el_w, vary=el_w_vary, min=el_w_min, max=el_w_max)
        #*********** inelastic lines *************************************************
        for i in xrange(len(self.exListRow)):
            row = self.exListRow[i]
            #****** Amplitude **********
            inel_A     = row.An_current.text()
            inel_A_min = row.An_min.text()
            inel_A_max = row.An_max.text()
            inel_A_fix = row.An_fix.isChecked()
            inel_A_vary= not(inel_A_fix)
            inel_A     = float(inel_A)
            inel_A_min = -np.inf if inel_A_min=="" else float(inel_A_min)
            inel_A_max =  np.inf if inel_A_max=="" else float(inel_A_max)
            self.pars_init.add("phonon_A_%d"%i, value=inel_A, vary=inel_A_vary, min=inel_A_min, max=inel_A_max)
            #****** Center **********
            inel_x0     = row.Cn_current.text()
            inel_x0_min = row.Cn_min.text()
            inel_x0_max = row.Cn_max.text()
            inel_x0_fix = row.Cn_fix.isChecked()
            inel_x0_vary= not(inel_x0_fix)
            inel_x0     = float(inel_x0)
            inel_x0_min = -np.inf if inel_x0_min=="" else float(inel_x0_min)
            inel_x0_max =  np.inf if inel_x0_max=="" else float(inel_x0_max)
            self.pars_init.add("phonon_E_%d"%i, value=inel_x0, vary=inel_x0_vary, min=inel_x0_min, max=inel_x0_max)
            #****** Width **********
            inel_w     = row.Wn_current.text()
            inel_w_min = row.Wn_min.text()
            inel_w_max = row.Wn_max.text()
            inel_w_fix = row.Wn_fix.isChecked()
            inel_w_vary= not(inel_w_fix)
            inel_w     = float(inel_w)
            inel_w_min = -np.inf if inel_w_min=="" else float(inel_w_min)
            inel_w_max =  np.inf if inel_w_max=="" else float(inel_w_max)
            self.pars_init.add("phonon_G_%d"%i, value=inel_w, vary=inel_w_vary, min=inel_w_min, max=inel_w_max)
        
    def fitting(self):
        self.fit_Label.show()
        self.init_params()
        self.FT = FittingThread(self)
        self.connect(self.FT, SIGNAL("resolution_missing"), self.resolution_missing)
        self.connect(self.FT, SIGNAL("fitting_done"), self.fitting_done)
        self.connect(self.FT, SIGNAL("finished()"), self.fit_Label.hide)
        self.FT.start()
    @QtCore.pyqtSlot()
    def fitting_done(self, fitObject):
        self.use_convolution = self.deconvolution_btn.isChecked()
        convolution = 1 if self.use_convolution else 0
        self.fitObject = fitObject
        if self.resolutionLoaded:
            self.deta = self.resolutionParams.res_param[self.analyser]
        else:
            self.deta = None
        mod = Spectrum_model(self.fitObject.result.params, self.energy, self.fitObject.shape, convolution=convolution, deta=self.deta, interpolation=0)
        self.ax.clear()
        self.ax.set_xlabel(self.MAIN_XLABEL, fontsize=15)
        self.ax.set_ylabel(self.MAIN_YLABEL, fontsize=15)
        self.ax.grid(True)
        self.ax.errorbar(self.energy, self.intensity, yerr=self.intensity_err, fmt="ko-",label="Exp. Data")
        self.ax.plot(mod.energy, mod.total_model, "r-", lw=1.5, label="Total model")
        self.ax.plot(mod.energy, mod.elastic_line, "g-", lw=1.5, label="Elastic line")
        for i in xrange(self.fitObject.num_excitation):
            self.ax.plot(mod.energy, mod.inelastic_lines[i], 'b-', lw=1.5, label="Excitation #%d"%(i+1))
        self.ax.set_xlim([self.energy.min(), self.energy.max()])
        self.ax.legend(loc="best")
        datafile_basename = os.path.basename(self.datafile)
        self.ax.set_title("%s - Analyser #%d"%(datafile_basename, self.analyser))
        self.canvas.draw()
        self.fitParamsDisplay.clear()
        self.fitParamsDisplay.appendPlainText(self.fitObject.result_text)
        # *************** Updating values on rows ***************************
        self.EL_amp_current.setText("%.2e"%self.fitObject.result.params["el_A"].value)
        self.EL_cen_current.setText("%.2f"%self.fitObject.result.params["el_x0"].value)
        self.EL_width_current.setText("%.2f"%self.fitObject.result.params["el_w"].value)
        self.BG_current.setText("%.2e"%self.fitObject.result.params["BG"].value)
        self.Temperature_current.setText("%.2f"%self.fitObject.result.params["T"].value)
        for i in xrange(self.fitObject.num_excitation):
            row = self.exListRow[i]
            row.An_current.setText("%.2e"%self.fitObject.result.params["phonon_A_%d"%i].value)
            row.Cn_current.setText("%.2f"%self.fitObject.result.params["phonon_E_%d"%i].value)
            row.Wn_current.setText("%.2f"%self.fitObject.result.params["phonon_G_%d"%i].value)
        
    @QtCore.pyqtSlot()
    def resolution_missing(self):
        self.messageBox = QtGui.QMessageBox()
        self.messageBox.setIcon(QtGui.QMessageBox.Critical)
        self.messageBox.setText("You didn't load the resolution functions. Please do it before fitting.")
        self.messageBox.setWindowTitle("Warning - Resolution functions missing...")
        self.messageBox.show()
        
    def extractSpec(self):
        self.extract_dialog=Extract_spec_Dialog()
        self.extract_dialog.show()
        
    def loadResolution(self):
        self.resolutionParamFile = QtGui.QFileDialog.getOpenFileName(self, "Load resolution parameters from file", self.current_folder)
        allowed_keys={"res_param":DictType,"T":FloatType}
        self.resolutionParams = read_resolution_file(str(self.resolutionParamFile), allowed_keys = allowed_keys)
        self.resolutionLoaded = True
        self.fitParamsDisplay.clear()
        txt = "Resolution parameters file: %s\n"%str(self.resolutionParamFile)
        txt+= "Ana# :[mu, Gaussian_width, Lorentzian_width]\n"
        for i in self.resolutionParams.res_param.keys():
            txt+= "%d : [%.6f, %.6f, %.6f]\n"%(i, self.resolutionParams.res_param[i][0], self.resolutionParams.res_param[i][1],self.resolutionParams.res_param[i][2])
        self.fitParamsDisplay.appendPlainText(txt)
        self.current_folder = os.path.dirname(str(self.resolutionParamFile))
        
    def help(self):
        self.helpDialog = Help_Dialog()
        self.helpDialog.show()
            

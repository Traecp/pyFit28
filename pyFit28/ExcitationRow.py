#!/usr/bin/python
# -*- coding: utf-8 -*-
from PyQt4 import QtGui, QtCore
class ExcitationRow(QtGui.QWidget):
    def __init__( self, num, parent):
        super(ExcitationRow, self).__init__()
        self.parent= parent
        self.rowLayout = QtGui.QGridLayout()
        self.rowLayout.setContentsMargins(0, 0, -1, 0)
        self.rowLayout.setVerticalSpacing(6)
        self.rowNum = num
        self.An = QtGui.QLabel("A%d"%self.rowNum)
        self.An.setMinimumSize(QtCore.QSize(25, 20))
        self.rowLayout.addWidget(self.An, 0, 0, 1, 1)
        
        self.An_current = QtGui.QLineEdit()
        self.An_current.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.An_current, 0, 1, 1, 1)
        
        self.An_min = QtGui.QLineEdit()
        self.An_min.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.An_min, 0, 2, 1, 1)
        
        self.An_max = QtGui.QLineEdit()
        self.An_max.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.An_max, 0, 3, 1, 1)
        
        self.An_fix = QtGui.QCheckBox("FIX")
        self.An_fix.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.An_fix, 0, 4, 1, 1)
        
        self.Cn = QtGui.QLabel("C%d"%self.rowNum)
        self.Cn.setMinimumSize(QtCore.QSize(25, 20))
        self.rowLayout.addWidget(self.Cn, 0, 5, 1, 1)
        
        self.Cn_current = QtGui.QLineEdit()
        self.Cn_current.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Cn_current, 0, 6, 1, 1)
        
        self.Cn_min = QtGui.QLineEdit()
        self.Cn_min.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Cn_min, 0, 7, 1, 1)
        
        self.Cn_max = QtGui.QLineEdit()
        self.Cn_max.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Cn_max, 0, 8, 1, 1)
        
        self.Cn_fix = QtGui.QCheckBox("FIX")
        self.Cn_fix.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Cn_fix, 0, 9, 1, 1)
        
        self.Wn = QtGui.QLabel("W%d"%self.rowNum)
        self.Wn.setMinimumSize(QtCore.QSize(25, 20))
        self.rowLayout.addWidget(self.Wn, 0, 10, 1, 1)
        
        self.Wn_current = QtGui.QLineEdit("0.1")
        self.Wn_current.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Wn_current, 0, 11, 1, 1)
        
        self.Wn_min = QtGui.QLineEdit("0.0")
        self.Wn_min.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Wn_min, 0, 12, 1, 1)
        
        self.Wn_max = QtGui.QLineEdit("10.0")
        self.Wn_max.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Wn_max, 0, 13, 1, 1)
        
        self.Wn_fix = QtGui.QCheckBox("FIX")
        self.Wn_fix.setMinimumSize(QtCore.QSize(40, 20))
        self.rowLayout.addWidget(self.Wn_fix, 0, 14, 1, 1)
        
        self.Remove_n = QtGui.QPushButton("Remove")
        self.Remove_n.setMinimumSize(QtCore.QSize(75, 25))
        self.rowLayout.addWidget(self.Remove_n, 0, 15, 1, 1)
        
        self.Remove_n.clicked.connect(self.destroyRow)
        
        self.setLayout(self.rowLayout)
    
    def destroyRow(self):
        self.parent.exRowNum += -1 
        self.deleteLater()
        self.parent.exListRow.remove(self.parent.exListRow[self.rowNum-1])
        # self.parent.markers[self.rowNum].pop(0).remove()
        # self.parent.markers[self.rowNum].remove()
        self.parent.ax.lines[self.parent.markers[self.rowNum]].remove()
        self.parent.markers.remove(self.parent.markers[self.rowNum])
        self.parent.canvas.draw()
        self.parent.peak_x.remove(self.parent.peak_x[self.rowNum])
        self.parent.peak_y.remove(self.parent.peak_y[self.rowNum])
        if self.parent.exRowNum >0:
            for i in xrange(self.parent.exRowNum):
                self.parent.exListRow[i].reset_number(i+1)
        
    def reset_number(self, num):
        self.rowNum = num
        self.An.setText("A%d"%self.rowNum)
        self.Cn.setText("C%d"%self.rowNum)
        self.Wn.setText("W%d"%self.rowNum)

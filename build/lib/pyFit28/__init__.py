#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui


def main():
    app = QtGui.QApplication(sys.argv)
    app.setOrganizationName('ESRF-ID28')
    app.setApplicationName('pyfit')
    app.setWindowIcon(QtGui.QIcon(":/icon"))
    from pyFit28.pyFit import Main
    main = Main()
    main.show()
    sys.exit(app.exec_())
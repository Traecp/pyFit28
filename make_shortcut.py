#!/usr/bin/env python

import os
import sys
import sysconfig
if sys.platform == 'win32':
    from win32com.client import Dispatch
homedir = os.path.expanduser("~")
__version__ = "2017.7.13"
__pyVersion__ = "py2.7"
version = __version__+"-"+__pyVersion__
def post_install(packageName):
    # Creates a Desktop shortcut to the installed software
    # For Windows only
    # Package name
    # packageName = 'mypackage'
    print "============ Creating shortcut =================="
    # Scripts directory (location of launcher script)
    scriptsDir = sysconfig.get_path('scripts')
    print "scriptsDir: ",scriptsDir
    libDir = sysconfig.get_path('platlib')
    iconPath = os.path.join(libDir, "pyFit28-%s.egg"%version, "pyFit28", "ui", "icons", "icon.ico")
    print "Icon path: ", iconPath

    # Target of shortcut
    target = os.path.join(scriptsDir, packageName + '.exe')
    print "Target path: ",target

    # Name of link file
    linkName = packageName + '.lnk'
    print "Link name: ",linkName

    # Read location of Windows desktop folder from registry
    regName = 'Desktop'
    regPath = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    desktopFolder = os.path.join(homedir,"Desktop")
    print "Desktop folder: ",desktopFolder

    # Path to location of link file
    pathLink = os.path.join(desktopFolder, linkName)
    print "pathlink: ",pathLink
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(pathLink)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = scriptsDir
    shortcut.IconLocation = iconPath
    shortcut.save()


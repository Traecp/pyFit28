#!/usr/bin/python
# -*- coding: utf-8 -*-
from make_shortcut import *
from setuptools import setup
import os, sys

pkgdata = {"":["icons/extract_2.png", "icons/help.png", "icons/loading.gif", "icons/open.png", "icons/quit.png", "icons/resolution.png", "icons/tick.png", "icons/wait.png", "icons/icon.ico", "icons/icon.png"]}
setup(
    name='pyFit28',
    version='2017.7.13',
    packages=['pyFit28', 'pyFit28.ui', 'pyFit28.ui.icons'],
    package_data=pkgdata,
    url='https://github.com/Traecp/pyFit28',
    license='GNU GENERAL PUBLIC LICENSE version 3',
    author='Tra Nguyen',
    author_email='thanh-tra.nguyen@esrf.fr',
    description='Fitting program for IXS spectra measured on ID28',
    entry_points={
        'gui_scripts': [
            'pyfit=pyFit28:main',
        ],
    },
    zip_safe=False,
    install_requires=[
        'matplotlib',
        'numpy',
        'scipy',
        'pymca5',
        'h5py',
        'lmfit',
    ]
)

if sys.argv[1] == 'install' and sys.platform == 'win32':
    post_install('pyfit')
elif sys.argv[1] == "install" and sys.platform.startswith("linux"):
    homedir = os.path.expanduser("~")
    desktopfolder = os.path.join(homedir, "Desktop")
    os.system("cp pyfit.desktop %s"%desktopfolder)
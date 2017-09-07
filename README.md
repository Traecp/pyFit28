# pyfit

A fitting program aims to fit IXS (inelastic X-ray scattering) spectra (phonon - to be more precised).

<img src="https://github.com/Traecp/pyFit28/blob/master/pyFit28_2.png">


INSTALLATION ON WINDOWS:
====================

 - Install Python 2.7 (I prefer to use Anaconda 64 bits)
 - Install PyQt4 (Anaconda comes with PyQt5 by default, please install PyQt4 by: *pip install -i https://pypi.anaconda.org/ales-erjavec/simple pyqt4)*
 - Other requirements (normally these will be automatically installed when you install pyfit): numpy >= 1.11, scipy >= 0.19, lmfit >= 0.9.5, matplotlib >= 1.5, h5py >=2.5.0 and PyMca5.
    If you have never installed PyMca5, you will need to install Microsoft Visual C++ compiler for Python 2.7 first. Please download and install vcpython27 here: http://aka.ms/vcpython27
    If PyMca5 fails to install: open a terminal and type: *pip install -U pymca5*
 - Download and extract the source code of pyFit28. Go to the folder where setup.py is found, open a terminal (command prompt on Windows) and type:
*python setup.py install* (on Linux you need to use *sudo* permission)


FOR NEWLY INSTALLED LINUX (TESTED ON DEBIAN AND UBUNTU):
====================

 - Install some dependencies which are useful for building future python packages (this is basically OpenGL): sudo apt-get install build-essential libgl1-mesa-dev freeglut3-dev
 - Install Anaconda for Python 2.7 -64bits (you can use the 32bits version if your machine is 32 bits). Instruction here: https://docs.continuum.io/anaconda/install/
 - Install PyQt4 with conda: conda install pyqt=4
 - For the moment PyMca5 requires fisx>=1.1.4, which is not built for linux (today we are 07/09/2017). Please download the source code of fisx and install it manually.
   The source code of fisx1.1.4 is here: https://github.com/vasole/fisx/archive/v1.1.4.tar.gz
   Extracting the archive, get inside the folder fisx-1.1.4 within a terminal and type: python setup.py install
 - Download the source code of pyFit28, extract it and install it with: python setup.py install 

MACOSX:
====================

 - Install Anaconda (Python 2.7, 64 bits if applicable)
 - Install PyQt4: https://pythonschool.net/pyqt/installing-pyqt-on-mac-os-x/
 - Download the source code of pyFit28, extract it and install it with: python setup.py install
 
 
RUN
====================

 - To run it: On both Linux and Windows, a shortcut is created on your Desktop, double click it to run this program. Otherwise you can open a terminal (command prompt) and type *pyfit*.


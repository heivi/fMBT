fMBT Windows version

Install
-------

* Choose fMBT installer for the same architecture as your Python. If
  you have 32-bit Python 2.7, use fMBT-installer-win32.exe. Print
  Python architecture:

  C:\Python27> python -c "import platform; print platform.architecture()"

  If you do not have Python, the installer that you choose will install
  Python 2.7.8 for the correct architecture, among other dependencies.

* Run fMBT-installer-winXX.exe.

* Let the installer install all (missing) dependencies and allow
  extending PATH.


Build
-----

* Run on Fedora 20:

  ./build-fMBT-installer-winXX.exe.sh 32
  or
  ./build-fMBT-installer-winXX.exe.sh 64

  to produce

  build-win32/fMBT-installer-win32.exe
  or
  build-win64/fMBT-installer-win64.exe.


Status
------

What is expected to work:

* fmbt (test generation and execution)

* fmbt-editor

* fmbt-scripter

* GUI test interfaces:

  - fmbtandroid

  - fmbtchromiumos

  - fmbttizen

  - fmbtwindows


What is likely to have issues (no porting efforts yet):

* GUI test interfaces: fmbtvnc, fmbtrdp


What is not planned to be ported on Windows:

* GUI test interfaces: fmbtx11
=======
fMBT Windows port is under development.

Currently certain GUI test interfaces can be used in Windows.

Building for Windows
--------------------

* Build requirements:

  - Visual C++ (tested with Visual Studio 2008 Express)

  - ImageMagick (tested with v6.8.9, 32-bit, 16bit colour depth):

    http://www.imagemagick.org/download/binaries/ImageMagick-6.8.9-4-Q16-x86-dll.exe

    (Install development libraries and header files)

  - Python 2 (tested with v2.7.7, 32bit):

    https://www.python.org/ftp/python/2.7.7/python-2.7.7.msi

  - fMBT sources, in this example under C:\src\fmbt


* Build:

  - C:\src\fmbt\utils>python setup.py bdist_wininst


* Install built package, for instance with 32-bit Python 2.7:

  - C:\src\fmbt\utils>dist\fmbt-python-VERSION-win32-py2.7.exe


Running on Windows
------------------

* Install:

  - ImageMagick (tested with prebuilt v6.8.9, 32-bit, with 16-bit colour depth):

    http://www.imagemagick.org/download/binaries/ImageMagick-6.8.9-4-Q16-x86-dll.exe

    (Let installed add utilities to system PATH, or add them manually)

  - Tesseract 3.02 or later (tested with v3.02.02, 32-bit)

    http://tesseract-ocr.googlecode.com/files/tesseract-ocr-setup-3.02.02.exe

  - Python 2 (tested with v2.7.7, 32bit):

    https://www.python.org/ftp/python/2.7.7/python-2.7.7.msi

  - fmbt-python-VERSION-*.exe (see Building for Windows)

* A script for testing that installation was successful:


# This test uses simulated GUI Test Connection, it does not synthesize
# real user events. "screenshot.png" should contain a screenshot, and
# "icon.png" an icon on it.

import fmbtgti
d = fmbtgti.GUITestInterface()
d.setConnection(fmbtgti.SimulatedGUITestConnection(["screenshot.png"])
d.refreshScreenshot()
print "OCR detected words:", d.screenshot().dumpOcr()
print "tapBitmap returns:", d.tapBitmap("icon.png")


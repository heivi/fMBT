# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This is library implements fmbtandroid.Device-like interface for
Tizen devices.

WARNING: THIS IS A VERY SLOW PROTOTYPE WITHOUT ANY ERROR HANDLING.
"""

import base64
import cPickle
import commands
import subprocess
import os
import sys

import fmbt
import fmbtgti

def _run(command, expectedExitStatus=None):
    if type(command) == str: shell=True
    else: shell=False

    try:
        p = subprocess.Popen(command, shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=True)
        if expectedExitStatus != None:
            out, err = p.communicate()
        else:
            out, err = ('', None)
    except Exception, e:
        class fakeProcess(object): pass
        p = fakeProcess
        p.returncode = 127
        out, err = ('', e)

    exitStatus = p.returncode

    if (expectedExitStatus != None and
        exitStatus != expectedExitStatus and
        exitStatus not in expectedExitStatus):
        msg = "Executing %s failed. Exit status: %s, expected %s" % (command, exitStatus, expectedExitStatus)
        fmbt.adapterlog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTTizenError(msg)

    return exitStatus, out, err

class Device(fmbtgti.GUITestInterface):
    def __init__(self):
        fmbtgti.GUITestInterface.__init__(self)
        self.setConnection(TizenDeviceConnection())

class TizenDeviceConnection(fmbtgti.GUITestConnection):
    def __init__(self):
        self._serialNumber = self.recvSerialNumber()
        self.connect()

    def connect(self):
        agentFilename = "/tmp/fmbttizen-agent.py"
        agentRemoteFilename = "/tmp/fmbttizen-agent.py"

        file(agentFilename, "w").write(_tizenAgent)

        status, _, _ = _run(["sdb", "push", agentFilename, agentRemoteFilename])

        self._sdbShell = subprocess.Popen(["sdb", "shell"], shell=False,
                                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                          close_fds=True)
        self._sdbShell.stdin.write("\r")
        ok, version = self._agentCmd("python %s; exit" % (agentRemoteFilename,))
        os.remove(agentFilename)
        return ok

    def close(self):
        self._sdbShell.stdin.close()
        self._sdbShell.stdout.close()
        self._sdbShell.terminate()

    def _agentWaitAnswer(self):
        errorLinePrefix = "FMBTAGENT ERROR "
        okLinePrefix = "FMBTAGENT OK "
        l = self._sdbShell.stdout.readline().strip()
        while True:
            if l.startswith(okLinePrefix):
                return True, cPickle.loads(base64.b64decode(l[len(okLinePrefix):]))
            elif l.startswith(errorLinePrefix):
                return False, cPickle.loads(base64.b64decode(l[len(errorLinePrefix):]))
            else:
                pass
            l = self._sdbShell.stdout.readline()
            if l == "": raise IOError("Unexpected end of sdb shell output")
            l = l.strip()

    def _agentCmd(self, command, retry=3):
        try:
            self._sdbShell.stdin.write("%s\r" % (command,))
            self._sdbShell.stdin.flush()
        except IOError:
            if retry > 0:
                self.connect()
                self._agentCmd(command, retry=retry-1)
            else:
                raise
        return self._agentWaitAnswer()

    def sendPress(self, keyName):
        return self._agentCmd("kp%s" % (keyName,))[0]

    def sendKeyDown(self, keyName):
        return self._agentCmd("kd%s" % (keyName,))[0]

    def sendKeyUp(self, keyName):
        return self._agentCmd("ku%s" % (keyName,))[0]

    def sendTap(self, x, y):
        return self._agentCmd("tt%s %s 1" % (x, y))[0]

    def sendTouchDown(self, x, y):
        return self._agentCmd("td%s %s 1" % (x, y))[0]

    def sendTouchMove(self, x, y):
        return self._agentCmd("tm%s %s" % (x, y))[0]

    def sendTouchUp(self, x, y):
        return self._agentCmd("tu%s %s 1" % (x, y))[0]

    def sendType(self, string):
        return self._agentCmd("kt%s" % (base64.b64encode(cPickle.dumps(string))))[0]

    def recvScreenshot(self, filename):
        remoteFilename = "/tmp/fmbttizen.screenshot.xwd"
        s, o = commands.getstatusoutput("sdb shell 'xwd -root -out %s'" % (remoteFilename,))
        s, o = commands.getstatusoutput("sdb pull %s %s.xwd" % (remoteFilename, filename))
        s, o = commands.getstatusoutput("sdb shell rm %s" % (remoteFilename,))
        s, o = commands.getstatusoutput("convert %s.xwd %s" % (filename, filename))
        os.remove("%s.xwd" % (filename,))
        return True

    def recvSerialNumber(self):
        s, o = commands.getstatusoutput("sdb get-serialno")
        return o.splitlines()[-1]

    def target(self):
        return self._serialNumber

# _tizenAgent code is executed on Tizen device in sdb shell.
# The agent synthesizes X events.
_tizenAgent = """
import base64
import cPickle
import ctypes
import os
import platform
import re
import struct
import sys
import time

libX11         = ctypes.CDLL("libX11.so")
libXtst        = ctypes.CDLL("libXtst.so.6")
X_CurrentTime  = ctypes.c_ulong(0)
X_True         = ctypes.c_int(1)
X_False        = ctypes.c_int(0)
X_NULL         = ctypes.c_char_p(0)
NoSymbol       = 0

display        = ctypes.c_void_p(libX11.XOpenDisplay(X_NULL))
current_screen = ctypes.c_int(-1)

# See struct input_event in /usr/include/linux/input.h
if platform.architecture()[0] == "32bit": _input_event = 'IIHHi'
else: _input_event = 'QQHHi'
# Event and keycodes are in input.h, too.
_EV_KEY = 0x01

# Set input device names (in /proc/bus/input/devices)
# for pressing hardware keys.
try: cpuinfo = file("/proc/cpuinfo").read()
except: cpuinfo = ""

if 'TRATS' in cpuinfo:
    # Running on Lunchbox
    hwKeyDevice = {
        "POWER": "/dev/input/event1",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "max8997-muic"
        }
    nonstandardKeycodes = {"HOME": 139}
elif 'QEMU Virtual CPU' in cpuinfo:
    # Running on Tizen emulator
    hwKeyDevice = {
        "POWER": "Power Button",
        "VOLUMEUP": "AT Translated Set 2 hardkeys",
        "VOLUMEDOWN": "AT Translated Set 2 hardkeys",
        "HOME": "AT Translated Set 2 hardkeys"
        }
    nonstandardKeycodes = {}
else:
    # Running on some other device
    hwKeyDevice = {
        "POWER": "msic_power_btn",
        "VOLUMEUP": "gpio-keys",
        "VOLUMEDOWN": "gpio-keys",
        "HOME": "mxt224_key_0"
        }
    nonstandardKeycodes = {}

# Read input devices
deviceToEventFile = {}
for _l in file("/proc/bus/input/devices"):
    if _l.startswith('N: Name="'): _device = _l.split('"')[1]
    elif _l.startswith("H: Handlers=") and "event" in _l:
        try: deviceToEventFile[_device] = "/dev/input/" + re.findall("(event[0-9]+)", _l)[0]
        except Exception, e: pass

# InputKeys contains key names known to input devices, see
# linux/input.h or http://www.usb.org/developers/hidpage. The order is
# significant, because keyCode = InputKeys.index(keyName).
InputKeys = [
    "RESERVED", "ESC","1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "MINUS", "EQUAL", "BACKSPACE", "TAB",
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "LEFTBRACE", "RIGHTBRACE", "ENTER", "LEFTCTRL",
    "A", "S", "D", "F", "G", "H", "J", "K", "L",
    "SEMICOLON", "APOSTROPHE", "GRAVE", "LEFTSHIFT", "BACKSLASH",
    "Z", "X", "C", "V", "B", "N", "M",
    "COMMA", "DOT", "SLASH", "RIGHTSHIFT", "KPASTERISK", "LEFTALT",
    "SPACE", "CAPSLOCK",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
    "NUMLOCK", "SCROLLLOCK",
    "KP7", "KP8", "KP9", "KPMINUS",
    "KP4", "KP5", "KP6", "KPPLUS",
    "KP1", "KP2", "KP3", "KP0", "KPDOT",
    "undefined0",
    "ZENKAKUHANKAKU", "102ND", "F11", "F12", "RO",
    "KATAKANA", "HIRAGANA", "HENKAN", "KATAKANAHIRAGANA", "MUHENKAN",
    "KPJPCOMMA", "KPENTER", "RIGHTCTRL", "KPSLASH", "SYSRQ", "RIGHTALT",
    "LINEFEED", "HOME", "UP", "PAGEUP", "LEFT", "RIGHT", "END", "DOWN",
    "PAGEDOWN", "INSERT", "DELETE", "MACRO",
    "MUTE", "VOLUMEDOWN", "VOLUMEUP",
    "POWER",
    "KPEQUAL", "KPPLUSMINUS", "PAUSE", "SCALE", "KPCOMMA", "HANGEUL",
    "HANGUEL", "HANJA", "YEN", "LEFTMETA", "RIGHTMETA", "COMPOSE"]

def read_cmd():
    return sys.stdin.readline().strip()

def write_response(ok, value):
    if ok: p = "FMBTAGENT OK "
    else: p = "FMBTAGENT ERROR "
    response = "%s%s\\n" % (p, base64.b64encode(cPickle.dumps(value)))
    sys.stdout.write(response)
    sys.stdout.flush()

def sendHwKey(inputDevice, keyCode, delayBeforePress, delayBeforeRelease):
    try: fd = os.open(inputDevice, os.O_WRONLY | os.O_NONBLOCK)
    except: return False
    if delayBeforePress > 0: time.sleep(delayBeforePress)
    if delayBeforePress >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 1)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
    if delayBeforeRelease > 0: time.sleep(delayBeforeRelease)
    if delayBeforeRelease >= 0:
        if os.write(fd, struct.pack(_input_event, int(time.time()), 0, _EV_KEY, keyCode, 0)) > 0:
            os.write(fd, struct.pack(_input_event, 0, 0, 0, 0, 0))
    os.close(fd)
    return True

def typeSequence(s):
    skipped = []
    for c in s:
        keysym = libX11.XStringToKeysym(c)
        if keysym == NoSymbol:
            skipped.append(c)
            continue
        keycode = libX11.XKeysymToKeycode(display, keysym)
        libXtst.XTestFakeKeyEvent(display, keycode, X_True, X_CurrentTime)
        libXtst.XTestFakeKeyEvent(display, keycode, X_False, X_CurrentTime)
    if skipped: return False, skipped
    else: return True, skipped

write_response(True, 0.0)
cmd = read_cmd()
while cmd:
    if cmd.startswith("tm"):   # touch move(x, y)
        xs, ys = cmd[2:].strip().split()
        libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
        libX11.XFlush(display)
        write_response(True, None)
    elif cmd.startswith("tt"): # touch tap(x, y, button)
        xs, ys, button = cmd[2:].strip().split()
        button = int(button)
        libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
        libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
        libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
        libX11.XFlush(display)
        write_response(True, None)
    elif cmd.startswith("td"): # touch down(x, y, button)
        xs, ys, button = cmd[2:].strip().split()
        button = int(button)
        libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
        libXtst.XTestFakeButtonEvent(display, button, X_True, X_CurrentTime)
        libX11.XFlush(display)
        write_response(True, None)
    elif cmd.startswith("tu"): # touch up(x, y, button)
        xs, ys, button = cmd[2:].strip().split()
        button = int(button)
        libXtst.XTestFakeMotionEvent(display, current_screen, int(xs), int(ys), X_CurrentTime)
        libXtst.XTestFakeButtonEvent(display, button, X_False, X_CurrentTime)
        libX11.XFlush(display)
        write_response(True, None)
    elif cmd.startswith("kd"): # hw key down
        rv = sendHwKey(deviceToEventFile[hwKeyDevice[cmd[2:]]], InputKeys.index(cmd[2:]), 0, -1)
        write_response(rv, None)
    elif cmd.startswith("kp"): # hw key press
        rv = sendHwKey(deviceToEventFile[hwKeyDevice[cmd[2:]]], InputKeys.index(cmd[2:]), 0, 0)
        write_response(rv, None)
    elif cmd.startswith("ku"): # hw key up
        rv = sendHwKey(deviceToEventFile[hwKeyDevice[cmd[2:]]], InputKeys.index(cmd[2:]), -1, 0)
        write_response(rv, None)
    elif cmd.startswith("kt"): # send x events
        rv, skippedSymbols = typeSequence(cPickle.loads(base64.b64decode(cmd[2:])))
        libX11.XFlush(display)
        write_response(rv, skippedSymbols)

    cmd = read_cmd()

display = libX11.XCloseDisplay(display)
"""

class FMBTTizenError(Exception): pass
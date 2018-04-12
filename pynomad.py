# MIT License
#
# Copyright (c) 2018 Justin Marple
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import serial
import time

class PyNomadException(Exception):
    pass

# Implements a simple class that allows for the nomad 883 by carbide3d to
# be controlled over a python script.
class PyNomad:
    def __init__(self):
        self.version = None
        self.version_number = None
        self.version_letter = None

        # Modal Groups
        self.motion_mode = 'G0'
        self.coordinate_system_select = 'G54'
        self.plane_select = 'G17'
        self.distance_mode = 'G90'
        self.arc_distance_mode = 'G91.1'
        self.units_mode = 'G21'
        self.cutter_radius_compensation = 'G40'
        self.tool_length_offset = 'G49'
        self.program_mode = 'M0'
        self.spindle_state = 'M5'
        self.coolant_state = 'M9'

        self.spindle_speed = 0
        self.feed_rate = 0

    def connect(self, serial_port, baud=115200):
        self._serial = serial.Serial(serial_port, baud, timeout=2)

        # First line is always blank, intentional?
        self._serial.readline()

        # Parses text for version number
        grbl_text = self._serial.readline()
        print "grbl_text = " + grbl_text
        #self.version = grbl_text.split()[1]
        #self.version_number = float(self.version[:3])
        #self.version_letter = self.version[3]

    def disconnect(self):
        self._serial.close()

    def status(self):
        self._serial.write(b'?')
        return self._serial.readline()

    def _move(self, x=None, y=None, z=None):
        command = ""
        if x != None:
            command = "X" + str(x)

        if y != None:
            command = command + "Y" + str(y)

        if z != None:
            command = command + "Z" + str(z)

        command = command + '\n'

        self._sendMessage(command)

    # Moves to absolute coordinates
    def moveTo(self, x=None, y=None, z=None):
        self.absoluteMode()
        self.linearMotionMode()
        self._move(x, y, z)

    def moveToFast(self, x=None, y=None, z=None):
        self.absoluteMode()
        self.rapidMotionMode()
        self._move(x, y, z)

    # Moves by relative coordinates 
    def moveBy(self, x=None, y=None, z=None):
        self.incrementalMode()
        self.linearMotionMode()
        self._move(x, y, z)

    def moveByFast(self, x=None, y=None, z=None):
        self.incrementalMode()
        self.rapidMotionMode()
        self._move(x, y, z)

    def _waitForReply(self, max_tries=50):

        # Sometimes other messages get sent before the "ok" or "error"
        # Try a few different lines until a response is found
        for i in range(0, max_tries):
            reply = self._serial.readline()

            print "Reply = " + str(reply)

            if 'ok' in reply: return True
            if 'error' in reply: raise PyNomadException(reply)

        raise PyNomadException("No Response From Machine")

    def _sendMessage(self, data):
        print "Sending = " + str(data)
        self._serial.flushInput()
        self._serial.flushOutput()
        self._serial.write(data)
        self._waitForReply()

    # Single line commands that expect "ok" or an error message back
    def unlock(self): self._sendMessage('$X\n')
    def home(self): self._sendMessage('$H\n')

    def spindleClockwise(self):
        self._sendMessage('M3\n')
        self.spindle_state = 'M3'

    def spindleCounterClockwise(self):
        self._sendMessage('M4\n')
        self.spindle_state = 'M4'

    def spindleStop(self):
        self._sendMessage('M5\n')
        self.spindle_state = 'M5'

    # Speed is an integer between 0-10000
    def spindleSpeed(self, speed):
        self._sendMessage('S' + str(int(speed)) + '\n')
        self.spindle_speed = int(speed)

    def feedRate(self, rate):
        self._sendMessage('F' + str(int(rate)) + '\n')
        self.feed_rate = int(rate)

    # Sets the units for the feedrate and x/y/z coordinates to be in
    def inInches(self):
        self._sendMessage('G20\n')
        self.units_mode = 'G20'

    def inMillimeters(self):
        self._sendMessage('G21\n')
        self.units_mode = 'G21'

    # Other available commands.  Advised to use moveTo and moveBy instead
    def absoluteMode(self):
        self._sendMessage('G90\n')
        self.distance_mode = 'G90'

    def incrementalMode(self):
        self._sendMessage('G91\n')
        self.distance_mode = 'G91'

    def rapidMotionMode(self):
        self._sendMessage('G0\n')
        self.motion_mode = 'G0'

    def linearMotionMode(self):
        self._sendMessage('G1\n')
        self.motion_mode = 'G1'

    # Waits until the status of the nomad is not 'Run'
    def waitUntilStopped(self, max_tries=50):

        try_counter = 0

        # Wait until movememnt is done
        while try_counter < max_tries:
            state = self.status().split(',')[0]
            if state != '<Run':
                break

            # We don't want to call '?' to often
            time.sleep(0.3)

            try_counter = try_counter + 1

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

from pynomad import PyNomad

if __name__ == '__main__':

    # Connect to the Nomad 883 over a com port.
    p = PyNomad()
    p.connect('COM23')

    # Unlock nomad 883 to start using it.  Alternatively, use the home method.
    #p.home()
    p.unlock()

    # Default settings
    p.inMillimeters()
    p.spindleSpeed(2000)
    p.spindleClockwise()
    p.feedRate(400)

    # Move by a relative position
    p.moveByFast(x=-10)
    p.moveByFast(x=10)
    p.moveBy(x=-5)
    p.moveBy(x=5)

    # moveTo functions can be either blocking or nonblocking, depending on the
    # the current state of the grbl buffer.  When you want to wait for the last
    # command to be executed, use waitUntilStopped()
    p.waitUntilStopped()

    # Move to absolute positions
    p.moveTo(x=-30, y=-20)
    p.moveTo(x=0, y=0)
    p.waitUntilStopped()

    # Stops the spindle from runnig.
    p.spindleStop()

    # Disconnect from COM port
    p.disconnect()

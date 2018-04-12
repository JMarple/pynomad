import serial
import threading

from enum import Enum
import time
class PyCarbideException(Exception):
    pass

GRBL_OK = 0

#
class PyCarbide(threading.Thread):
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
        '''self.version = grbl_text.split()[1]
        self.version_number = float(self.version[:3])
        self.version_letter = self.version[3]'''

    def disconnect(self):
        self._serial.close()

    def status(self):
        self._serial.write(b'?')
        for i in range(0, 6):
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

    def moveTo(self, x=None, y=None, z=None):
        self.absoluteMode()
        self.linearMotionMode()
        self._move(x, y, z)

    def moveToFast(self, x=None, y=None, z=None):
        self.absoluteMode()
        self.rapidMotionMode()
        self._move(x, y, z)

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

            if 'ok' in reply: return True
            if 'error' in reply: raise PyCarbideException(reply)

        raise PyCarbideException("No Response From Machine")

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

    def inInches(self):
        self._sendMessage('G20')
        self.units_mode = 'G20'

    def inMillimeters(self):
        self._sendMessage('G21')
        self.units_mode = 'G21'

    # Other available commands
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


def rotateGear(s, amount):
    output = 'P ' + str(amount) + '\n'
    print "Outputing: " + output
    s.write(output)

def waitForRotate(s):
    time.sleep(0.3)
    s.flushInput()

    while True:
        s.write('S\n')
        speed = s.readline()
        #print repr(speed)
        speed = float(speed)
        if speed < 0.01: return
        time.sleep(0.1)

def getIndicatorReading(s):
    s.write('T\n');

    return raw_input("Enter indicator reading:");

def cut_tooth(p, depth, height):
    p.feedRate(40)

    print "Cutting tooth with depth %f" % depth
    print "height is %f" % height

    trav_by = 9

    #p.spindleSpeed(2000)
    #p.spindleClockwise()
    p.moveByFast(y=-1)
    p.moveBy(z=height)
    p.moveBy(y=-depth)
    p.moveBy(x=-trav_by)
    #p.moveBy(x=5)
    p.moveBy(y=depth)
    p.moveBy(z=-height)
    p.moveByFast(y=1)
    p.moveByFast(x=trav_by)

    # Wait until movememnt is done
    while True:
        state = p.status().split(',')[0]
        if state != '<Run':
            break

        time.sleep(0.3)
    #p.spindleStop()

def measureRunout(s, num_teeth, ticks_per_rotation):
    indicator_readings = [0] * num_teeth

    for i in range(0, num_teeth):
        rotateGear(r, ticks_per_rotation / num_teeth)
        waitForRotate(r)
        reading = getIndicatorReading(r)

        indicator_readings[i] = reading

    return indicator_readings

if __name__ == "__main__":

    r = serial.Serial('/dev/ttyACM1', 9600, timeout=20)

    #print "Done"

    p = PyCarbide()
    p.connect('/dev/ttyACM0')
    p.unlock()

    num_teeth = 40
    ticks_per_rotation = 48000

    runout = measureRunout(r, num_teeth, ticks_per_rotation)
    #runout = ['0.00', '0.00', '-0.01', '-0.02', '0.02', '0.01', '0.05', '0.06', '0.09', '0.14', '0.16', '0.20', '0.25', '0.28', '0.31', '0.34', '0.39', '0.42', '0.46', '0.50', '0.52', '0.54', '0.55', '0.56', '0.56', '0.54', '0.52', '0.49', '0.47', '0.43', '0.38', '0.34', '0.28', '0.25', '0.20', '0.12', '0.10', '0.06', '0.04', '0.01']
    #runout = [0] * num_teeth

    print runout
    var = raw_input("Attach gear and press enter to start milling")

    p.spindleSpeed(10000)
    p.spindleClockwise()

    starting_depth = 0

    for i in range(0, num_teeth):
        tooth_depth = 0.675
        j = i + num_teeth/2
        if j >= num_teeth:
            j -= num_teeth

        offset_90 = (i + num_teeth/4) % num_teeth
        offset_180 = (i + num_teeth/2) % num_teeth
        offset_270 = (i + 3 * num_teeth / 4) % num_teeth

        rotateGear(r, ticks_per_rotation/num_teeth)
        time.sleep(1)
        waitForRotate(r)

        height_runout =(
            (float(runout[offset_90]) + float(runout[offset_270])) / 2.0)

        if (i == 0):
            starting_depth = float(runout[offset_180])

        cut_tooth(p, tooth_depth - float(runout[offset_180]) + starting_depth, height_runout)

    #p.home()

    #p.spindleSpeed(5000)
    #p.spindleClockwise()


    '''p.moveToFast(x=-30, y=-(69.62)-6.1, z=-82.28-5)

    var = raw_input("ADD DRILL BIT")

    for i in range(0, 42):
        cut_tooth(p)

        var = raw_input("Rotate Gear")
        rotateGear(r, 1000)
        time.sleep(7)

    var = raw_input("REMOVE DRILL BIT")

    p.moveToFast(x=-10, y=-10, z=-10)

    var = raw_input("Press Enter to continue")

    #p.status()'''

    p.disconnect()

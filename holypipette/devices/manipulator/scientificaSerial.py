import serial
from .manipulator import Manipulator
import time

__all__ = ['ScientificaSerial']

class SerialCommands():
    GET_X_POS = 'PX\r'
    GET_Y_POS = 'PY\r'
    GET_Z_POS = 'PZ\r'
    GET_X_Y_Z = '\r'
    GET_MAX_SPEED = 'TOP\r'
    GET_MAX_ACCEL = 'ACC\r'
    GET_IS_BUSY = 's\r'

    SET_X_Y_POS_ABS = 'abs {} {}\r'
    SET_X_Y_POS_REL = 'rel {} {}\r'

    SET_Z_POS = 'absz {}\r'
    SET_MAX_SPEED = 'TOP {}\r'
    SET_MAX_ACCEL = 'ACC {}\r'

    STOP = 'STOP\r'

class ScientificaSerial(Manipulator):

    def __init__(self, comPort: serial.Serial):
        self.comPort : serial.Serial = comPort
        self.set_max_accel(100)
        self.set_max_speed(10000)
    
    def set_max_speed(self, speed):
        '''Sets the max speed for the Scientifica Stage.  
           It seems like the range for this is around (1000, 100000)
        '''
        self._sendCmd(SerialCommands.SET_MAX_SPEED.format(int(speed)))

    def set_max_accel(self, accel):
        '''Sets the max acceleration for the Scientifica Stage.
           It seems like the range for this is around (10, 10000)
        '''
        self._sendCmd(SerialCommands.SET_MAX_ACCEL.format(int(accel)))

    def __del__(self):
        self.comPort.close()

    def _sendCmd(self, cmd):
        self.comPort.write(cmd.encode())
        time.sleep(0.05) #TODO: replace with something better

        resp = self.comPort.read_until(b'\r') #read reply to message
        resp = resp[:-1]
        return resp.decode()

    def position(self, axis=None):
        if axis == 1:
            xpos = self._sendCmd(SerialCommands.GET_X_POS)
            return int(xpos) / 10.0
        if axis == 2:
            ypos = self._sendCmd(SerialCommands.GET_Y_POS)
            return int(ypos) / 10.0
        if axis == 3:
            zpos = self._sendCmd(SerialCommands.GET_Z_POS)
            return int(zpos) / 10.0
        if axis == None:
            xyz = self._sendCmd(SerialCommands.GET_X_Y_Z).split(b'\t')
            
            xPos = int(xyz[0]) / 10.0
            yPos = int(xyz[1]) / 10.0
            zPos = int(xyz[2]) / 10.0

            return [xPos, yPos, zPos]

    def absolute_move(self, pos, axis):
        if axis == 1:
            yPos = self.position(axis=2)
            self._sendCmd(SerialCommands.SET_X_Y_POS_ABS.format(int(pos * 10) , int(yPos * 10)))
        if axis == 2:
            xPos = self.position(axis=1)
            self._sendCmd(SerialCommands.SET_X_Y_POS_ABS.format(int(xPos * 10), int(pos * 10)))
        if axis == 3:
            self._sendCmd(SerialCommands.SET_Z_POS.format(int(pos * 10)))
    
    def absolute_move_group(self, x, axes):
        x = list(x)
        axes = list(axes)
        if 1 in axes and 2 in axes:
            xPos = x[axes.index(1)]
            yPos = x[axes.index(2)]
            print("sent cmd", xPos, yPos)
            self._sendCmd(SerialCommands.SET_X_Y_POS_ABS.format(int(xPos * 10), int(yPos * 10)))
        else:
            print(f'unimplemented move group {x} {axes}')
    
    def relative_move_group(self, pos, axis):
        if axis == 1:
            self._sendCmd(SerialCommands.SET_X_Y_POS_REL.format(pos, 0))
        if axis == 2:
            self._sendCmd(SerialCommands.SET_X_Y_POS_REL.format(0, pos))
        if axis == 3:
            currZ = self.position(3)
            self._sendCmd(SerialCommands.SET_Z_POS.format(int((currZ + pos) * 10)))

    def relative_move_group(self, x, axes):
        cmd = [0, 0, 0]
        for pos, axis in zip(x, axes):
            cmd[axis  - 1] = pos
        
        if cmd[0] != 0 or cmd[1] != 0:
            self._sendCmd(SerialCommands.SET_X_Y_POS_REL.format(int(cmd[0] * 10), int(cmd[1] * 10)))

        if cmd[2] != 0:
            currZ = self.position(3)
            self._sendCmd(SerialCommands.SET_Z_POS.format(int((currZ + cmd[2]) * 10)))

    def wait_until_still(self, axes = None, axis = None):
        while True:
            resp = self._sendCmd(SerialCommands.GET_IS_BUSY)
            busy = resp != '0'

            if not busy:
                break

    def stop(self):
        self._sendCmd(SerialCommands.STOP)
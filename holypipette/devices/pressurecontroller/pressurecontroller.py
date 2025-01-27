'''
A general pressure controller class
'''
import collections
import time

from holypipette.controller.base import TaskController

all = ['PressureController',  'FakePressureController']


class PressureController(TaskController):
    def __init__(self):
        super(PressureController, self).__init__()
        self._pressure = collections.defaultdict(int)

    def measure(self, port = 0):
        '''
        Measures the instantaneous pressure, on designated port.
        '''
        pass

    def set_pressure(self, pressure, port = 0):
        '''
        Sets the pressure, on designated port.
        '''
        self._pressure[port] = pressure

    def get_pressure(self, port=0):
        '''
        Gets the pressure on the designated port. Note that this does not refer
        to any measurement, but simply to the pressure as set via
        `.set_pressure`.
        '''
        return self._pressure[port]

    def ramp(self,amplitude = -230., duration = 1.5, port = 0):
        '''
        Makes a ramp of pressure
        '''
        t0 = time.time()
        t = t0
        while t-t0<duration:
            self.set_pressure(amplitude*(t-t0)/duration)
            time.sleep(0.05)
            t = time.time()
        self.set_pressure(0.)


class FakePressureController(PressureController):
    def __init__(self):
        super(FakePressureController, self).__init__()
        self.pressure = 0

    def measure(self, port=0):
        '''
        Measures the instantaneous pressure, on designated port.
        '''
        return self.pressure

    def set_pressure(self, pressure, port=0):
        '''
        Sets the pressure, on designated port.
        '''
        self.debug('Pressure set to: {}'.format(pressure))
        self.pressure = pressure

    def get_pressure(self, port=0):
        return self.pressure

'''
Control of manipulators with gamepad

TODO:
- axis signs should be stored rather than passed as parameters?
- Command line argument: configuration file

Note: relative move takes time to stop in fast mode.
'''
from holypipette.devices.gamepad import *
import os
import time
from holypipette.devices.manipulator.luigsneumann_SM10 import LuigsNeumann_SM10
import numpy as np

class GamepadController(GamepadProcessor):
    def __init__(self, gamepad_reader, dev, config=None):
        self.dev = dev
        super(GamepadController, self).__init__(gamepad_reader, config=config)
        self.current_MP = 0
        self.locked = [False]*self.how_many_MP
        self.all_locked = False
        #self.memory = None # should be in configuration file
        self.calibration_position = [None]*self.how_many_MP
        #self.dzdx = [0.]*how_many_MP # movement in z for a unit movement in x
        self.withdrawn = False
        self.high_speed = False
        self.low_speed = False

        for i in range(1,10):
            self.dev.set_single_step_velocity(i, 12)

    def load(self, config=None):
        super(GamepadController, self).load(config)
        self.MP_axes = self.config["axes"]['manipulators']
        self.stage_axes = self.config["axes"]['stage']
        self.focus_axis = self.config["axes"]['focus']
        self.how_many_MP = len(self.config['axes']['manipulators'])
        #self.dzdx = self.config.get('dzdx', [0.]*self.how_many_MP) # maybe as angle?
        self.dzdx = np.sin(np.pi/180*np.array(self.config.get('angle', [0.] * self.how_many_MP))) # maybe as angle?
        self.memory = self.config.get('memory', None)
        if self.memory is None:
            self.memorize()

    def save(self):
        #self.config['dzdx'] = self.dzdx
        self.config['angle'] = [float(x) for x in np.arcsin(np.array(self.dzdx))*180/np.pi]
        self.config['memory'] = [float(x) for x in self.memory]
        super(GamepadController, self).save()

    def buffered_relative_move(self, x, axis, fast=False):
        '''
        Issues a relative move only if the axis already doing that movement.
        '''
        if x != self.current_move:
            if self.current_move != 0.:
                self.dev.stop(axis)
            if x!= 0.:
                self.dev.relative_move(x, axis, fast=fast)
            self.current_move = x

    def quit(self):
        self.terminated = True

    def high_speed_on(self):
        self.high_speed = True

    def high_speed_off(self):
        self.high_speed = False

    def low_speed_on(self):
        self.low_speed = True

    def low_speed_off(self):
        self.low_speed = False

    def select_manipulator(self):
        self.current_MP = (self.current_MP + 1) % self.how_many_MP
        print('Selected manipulator:', self.current_MP+1)

    def lock_MP(self):
        self.locked[self.current_MP] = not self.locked[self.current_MP]
        print('Manipulator', self.current_MP, 'lock:', self.locked[self.current_MP])

    def lock_all_MP(self):
        if all(self.locked):
            self.locked = [False]*self.how_many_MP
            print('Manipulator unlocked')
        else:
            self.locked = [True] * self.how_many_MP
            print('Manipulator locked')

    def calibrate(self):
        print('Calibrate')
        position = self.dev.position_group(self.MP_axes[self.current_MP])
        if self.calibration_position[self.current_MP] is not None:
            dx, dz = position[0] - self.calibration_position[self.current_MP][0], position[2] - self.calibration_position[self.current_MP][2]
            if dx != 0:
                self.dzdx[self.current_MP] = dz/dx
                print(dz/dx)
        self.calibration_position[self.current_MP] = position

    def go_to_memorized(self):
        print('Go to')
        self.dev.absolute_move_group(self.memory, self.stage_axes+[self.focus_axis])

    def memorize(self):
        print('Memorize')
        self.memory = self.dev.position_group(self.stage_axes+[self.focus_axis])

    def withdraw(self, direction):
        print('Withdraw')
        direction = float(direction)
        if self.withdrawn:
            self.withdrawn = False
            self.dev.relative_move(-direction, self.MP_axes[self.current_MP][0], fast=True)
        else:
            self.withdrawn = True
            self.dev.relative_move(direction, self.MP_axes[self.current_MP][0], fast=True)
        print('done')

    def stop_withdraw(self):
        print('Aborting')
        self.dev.stop(self.MP_axes[self.current_MP][0])

    def MP_virtualX_Y(self, X, Y, directionX, directionY):
        X = X*float(directionX)
        Y = Y * float(directionY)
        if (X!=0.) or (Y!=0.):
            print('MP',X,Y)
            dzdx = self.dzdx[self.current_MP]
            X = X/(1+dzdx**2)**.5
            Z = X*dzdx/(1+dzdx**2)**.5
            for i, d in enumerate([X,Y,Z]):
                self.dev.set_single_step_distance(self.MP_axes[self.current_MP][i], d)
                self.dev.single_step(self.MP_axes[self.current_MP][i], 1)

    def stage_XY(self, X, Y, directionX, directionY):
        X, Y = self.discrete_state(X, Y)
        X = X*float(directionX)
        Y = Y * float(directionY)

        print('Stage speed move', X, Y, ', high speed = ', self.high_speed)
        self.buffered_relative_move(X, self.stage_axes[0], fast=self.high_speed)

    def MP_fine_XZ(self, X, Z, directionX, directionZ):
        X, Z = self.discrete_state(X, Z)
        X = X*float(directionX)
        Z = Z * float(directionZ)

        self.buffered_relative_move(X, self.MP_axes[self.current_MP][0], fast=self.high_speed)
        self.buffered_relative_move(Z, self.MP_axes[self.current_MP][2], fast=self.high_speed)
        # Locked movements
        if self.locked[self.current_MP]:
            dzdx = self.dzdx[self.current_MP]
            self.buffered_relative_move(Z, self.MP_axes[self.focus_axis], fast=self.high_speed)
            #self.focus(1., Z + X*dzdx) # or the opposite? # can only work with steps
            # if others are locked, move them too
            if all(self.locked):
                current_MP = self.current_MP
                for i in range(len(self.locked)):
                    if i!= current_MP:
                        self.current_MP = i
                        self.buffered_relative_move(Z, self.MP_axes[self.current_MP][2], fast=self.high_speed)
                self.current_MP = current_MP

    def focus(self, Z, direction): # could be a relative move too
        Z = Z*float(direction)
        if Z!=0.:
            print('Focus',Z)
            self.dev.set_single_step_distance(self.focus_axis, Z)
            self.dev.single_step(self.focus_axis, 1)

    # def MP_Z(self, direction):
    #     d = float(direction)
    #     print('MP Z', d)
    #     if d == 0.: # abort
    #         print("aborting")
    #         self.dev.stop(self.MP_axes[self.current_MP][2])
    #     else:
    #         print('relative move', d)
    #         self.dev.relative_move(d, self.MP_axes[self.current_MP][2], fast=False)

    def MP_Z_step(self, direction):
        d = float(direction)
        self.dev.set_single_step_distance(self.MP_axes[self.current_MP][2], d)
        self.dev.single_step(self.MP_axes[self.current_MP][2], 1)
        if self.locked[self.current_MP]:
            self.focus(1., direction) # might not be the right direction!
            # if others are locked, move them too
            if all(self.locked):
                current_MP = self.current_MP
                for i in range(len(self.locked)):
                    if i!= current_MP:
                        self.current_MP = i
                        self.MP_Z_step(direction) # might not be the right direction!
                self.current_MP = current_MP


dev = LuigsNeumann_SM10(stepmoves=False)
reader = GamepadReader()
reader.start()
gamepad = GamepadController(reader, dev, config='~/PycharmProjects/holypipette/development/gamepad.yaml')
gamepad.start()
gamepad.join()
reader.stop()

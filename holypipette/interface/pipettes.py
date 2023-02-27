# coding=utf-8
import pickle
import os

import numpy as np
from PyQt5 import QtCore

from holypipette.interface import TaskInterface, command, blocking_command
from holypipette.devices.manipulator.calibratedunit import CalibratedUnit, CalibratedStage, CalibrationConfig
import time

class PipetteInterface(TaskInterface):
    '''
    Controller for the stage, the microscope, and several pipettes.
    '''

    def __init__(self, stage, microscope, camera, unit,
                 config_filename=None):
        super(PipetteInterface, self).__init__()
        self.microscope = microscope
        self.camera = camera
        # Create a common calibration configuration for all stages/manipulators
        self.calibration_config = CalibrationConfig(name='Calibration')
        self.calibrated_stage = CalibratedStage(stage, None, microscope, camera,
                                                config=self.calibration_config)
        self.calibrated_unit = CalibratedUnit(unit,
                                                self.calibrated_stage,
                                                microscope,
                                                camera,
                                                config=self.calibration_config)

        # This should be refactored (in TaskInterface?)
        config_folder = os.path.join(os.path.expanduser('~'),'holypipette')
        if not os.path.exists(config_folder):
            os.mkdir(config_folder)
        if config_filename is None:
            config_filename = 'config_manipulator.cfg'
        config_filename = os.path.join(config_folder,config_filename)

        self.config_filename = config_filename
        self.cleaning_bath_position = None
        self.contact_position = None
        self.rinsing_bath_position = None
        self.paramecium_tank_position = None
        self.timer_t0 = time.time()

    def connect(self, main_gui):
        pass #TODO: unused?

    @command(category='Manipulators',
             description='Move pipette in x direction by {:.0f}μm',
             default_arg=10)
    def move_pipette_x(self, distance):
        self.calibrated_unit.relative_move(distance, axis=0)

    @command(category='Manipulators',
             description='Move pipette in y direction by {:.0f}μm',
             default_arg=10)
    def move_pipette_y(self, distance):
        self.calibrated_unit.relative_move(distance, axis=1)

    @command(category='Manipulators',
             description='Move pipette in z direction by {:.0f}μm',
             default_arg=10)
    def move_pipette_z(self, distance):
        self.calibrated_unit.relative_move(distance, axis=2)

    @command(category='Microscope',
             description='Move microscope by {:.0f}μm',
             default_arg=10)
    def move_microscope(self, distance):
        self.microscope.relative_move(distance)

    @command(category='Microscope',
             description='Set the position of the floor (cover slip)',
             success_message='Cover slip position stored')
    def set_floor(self):
        self.microscope.floor_Z = self.microscope.position()

    @command(category='Stage',
             description='Move stage vertically by {:.0f}μm',
             default_arg=10)
    def move_stage_vertical(self, distance):
        self.calibrated_stage.relative_move(distance, axis=1)

    @command(category='Stage',
             description='Move stage horizontally by {:.0f}μm',
             default_arg=10)
    def move_stage_horizontal(self, distance):
        self.calibrated_stage.relative_move(distance, axis=0)

    @blocking_command(category='Stage',
                      description='Calibrate stage only',
                      task_description='Calibrating stage')
    def calibrate_stage(self):
        self.execute([self.calibrated_stage.calibrate])

    @blocking_command(category='Stage',
                    description='Create a Mosaic image',
                    task_description='Create a Mosaic Image')
    def create_mosaic(self):
        self.execute(self.calibrated_stage.mosaic)


    @blocking_command(category='Manipulators',
                      description='Calibrate manipulator',
                      task_description='Calibrating manipulator')
    def calibrate_manipulator(self):
        self.execute([self.calibrated_unit.calibrate])

    @blocking_command(category='Manipulators',
                      description='Focus the pipette',
                      task_description='Calibrating manipulator')
    def focus_pipette(self):
        self.execute([self.calibrated_unit.autofocus_pipette])

    @blocking_command(category='Manipulators',
                      description='Recalibrate manipulator',
                      task_description='Recalibrating manipulator')
    def recalibrate_manipulator(self):
        self.execute(self.calibrated_unit.recalibrate)

    @blocking_command(category='Manipulators',
                     description='Recalibrate manipulator',
                     task_description='Recalibrate manipulator at click position')
    def recalibrate_manipulator_on_click(self, xy_position):
        self.debug('asking for recalibration at {}'.format(xy_position))
        self.execute(self.calibrated_unit.recalibrate, argument=xy_position)

    @blocking_command(category='Manipulators',
                     description='Move pipette to position',
                     task_description='Moving to position with safe approach')
    def move_pipette(self, xy_position):
        x, y = xy_position
        position = np.array([x, y, self.microscope.position()])
        self.debug('asking for safe move to {}'.format(position))
        self.execute(self.calibrated_unit.safe_move, argument=position)

    @blocking_command(category='Manipulators',
                     description='Move stage to position',
                     task_description='Moving stage to position')
    def move_stage(self, xy_position):
        x, y = xy_position
        position = np.array([x, y])
        self.debug('asking for reference move to {}'.format(position))
        self.execute(self.calibrated_stage.reference_relative_move, argument=-position) # compensatory move

    @blocking_command(category='Microscope',
                      description='Go to the floor (cover slip)',
                      task_description='Go to the floor (cover slip)')
    def go_to_floor(self):
        if self.microscope.floor_Z is None:
            raise RuntimeError("Coverslip floor must be set.")
        self.execute(self.microscope.absolute_move,
                     argument=self.microscope.floor_Z)
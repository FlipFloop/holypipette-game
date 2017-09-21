'''
This is a test GUI, to test the functionality.

Seems to work, except the camera apparently doesn't start until waitkey (??)
'''
from devices import *
from vision import *
from gui import *
import cv2
import time
from numpy import array

def callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        xs = x-camera.width/2
        ys = y-camera.height/2
        print xs, ys
        #calibrated_stage.reference_move(calibrated_stage.reference_position()-array([xs, ys, 0]))
        calibrated_unit.reference_move(array([xs, ys, 0]))

#camera = OpenCVCamera()
camera = Lumenera()
video = LiveFeed(camera, mouse_callback=callback)

controller = LuigsNeumann_SM10()
stage = ManipulatorUnit(controller,[7,8])
microscope = Microscope(controller,9)
calibrated_stage = CalibratedStage(stage, None, microscope, camera=camera)
unit = ManipulatorUnit(controller, [1,2,3])
calibrated_unit = CalibratedUnit(unit, None, microscope, camera=camera)

u0 = unit.position()

def message(msg):
    print msg

try:

    cv2.waitKey(0)

    #t1 = time.time()
    #calibrated_stage.calibrate()
    #t2 = time.time()
    #print "Calibration took",t2-t1,"s"
    #print calibrated_stage.M, calibrated_stage.r0

    t1= time.time()
    calibrated_unit.calibrate(message)
    t2 = time.time()
    print t2-t1,'s'

    cv2.waitKey(0)

finally:
    unit.absolute_move(u0)
    video.stop()

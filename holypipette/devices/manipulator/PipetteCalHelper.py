import time
import cv2
import numpy as np
from holypipette.devices.manipulator.microscope import Microscope
from holypipette.devices.manipulator import Manipulator
from holypipette.devices.camera import Camera
from holypipette.deepLearning.pipetteFinder import PipetteFinder
from threading import Thread

class PipetteCalHelper():
    '''A helper class to aid with Pipette Calibration
    '''
    
    CAL_MAX_SPEED = 1000
    NORMAL_MAX_SPEED = 10000

    def __init__(self, pipette: Manipulator, camera: Camera):
        self.pipette : Manipulator = pipette
        self.camera : Camera = camera
        self.pipetteFinder : PipetteFinder = PipetteFinder()
        self.lastFrameNo = 0 #the last frame we've recorded when moving the pipette

    def calibrateContinuous(self, distance, axis):
        '''Tell the stage to go a certain distance at a low max speed.
           Take a bunch of pictures and use optical flow. Use optical flow information
           to create a linear transform from stage microns to image pixels. 
        '''

        #first, make sure the pipette is in frame
        _, _, _, frame = self.camera._last_frame_queue[0]
        pos = self.pipetteFinder.find_pipette(frame)
        if pos is None:
            raise RuntimeError("pipette must be in frame for pipette calibration!")

        #move the pipette a certain distance forward and up
        initPos = self.pipette.position()
        cmd = initPos.copy()
        cmd[axis] += distance

        #note: the "axis" for absolute_move is 0 indexed b/c it's indexing into the array of device axes in manipulatorunit.py.  This should be refactored later for consistency
        self.pipette.absolute_move(cmd[axis], axis) 
        
        framesAndPoses = []

        #wait for the pipette to reach the pos. Record frames and pos as the pipette moves
        currPos = self.pipette.position()
        while abs(currPos[0] - cmd[0]) > 1 or abs(currPos[1] - cmd[1]) > 1:

            while self.lastFrameNo == self.camera.get_frame_no():
                time.sleep(0.01) #wait for a new frame to be read from the camera
            self.lastFrameNo = self.camera.get_frame_no()
            currPos = self.pipette.position()
            
            #get latest img and pipette pos, add to arr
            _, _, _, frame = self.camera._last_frame_queue[0]
            framesAndPoses.append((frame, currPos))
            print(f"haven't reached yet... {currPos} {cmd}")

        #find the pipette in all the frames
        pixelsAndPoses = []
        for i, (frame, pipettePos) in enumerate(framesAndPoses):
            if i % 30 == 0:
                print(f"determining pipette path... {i * 100 / len(framesAndPoses) :.2f}%")
            imgPos = self.pipetteFinder.find_pipette(frame)
            if imgPos is not None:
                pixelsAndPoses.append([imgPos[0], imgPos[1], pipettePos[0], pipettePos[1]])
        
        pixelsAndPoses = np.array(pixelsAndPoses)

        #for some reason, estimateAffinePartial2D only works with int64
        #we can multiply by 100, to preserve 2 decimal places without affecting rotation / scaling portion of affline transform
        pixelsAndPoses = (pixelsAndPoses.copy()).astype(np.int64) 
        print(pixelsAndPoses)

        #move pipette back to starting pos
        self.pipette.absolute_move(initPos[axis], axis)
        self.pipette.wait_until_still()

        return pixelsAndPoses

    def calibrate(self, dist=2500):
        '''Calibrates the pipette using YOLO object detection and pipette encoders to create a um -> pixels transformation matrix
        '''
        
        self.pipette.set_max_speed(self.CAL_MAX_SPEED)
        initPos = self.pipette.position()

        for axis in range(2):
            pixelsAndPoses = self.calibrateContinuous(dist, axis)
            if axis == 0:
                pixelsAndPosesX = pixelsAndPoses
            else:
                pixelsAndPosesY = pixelsAndPoses

        # use ransac to fit a linear transform from pixels to stage position
        xmat, _ = cv2.estimateAffinePartial2D(pixelsAndPosesX[:,2:4], pixelsAndPosesX[:,0:2])
        ymat, _ = cv2.estimateAffinePartial2D(pixelsAndPosesY[:,2:4], pixelsAndPosesY[:,0:2])


        #combine the two transforms into one
        mat = np.zeros((2,3))
        mat[0:2,0] = xmat[0:2,0] #combine column vectors
        mat[0:2,1] = ymat[0:2,1]
        mat[0,2] = xmat[0,2] #combine offsets
        mat[1,2] = ymat[1,2]

        alt, _ = cv2.estimateAffine2D(np.append(pixelsAndPosesY[:,2:4], pixelsAndPosesX[:,2:4], axis=0), np.append(pixelsAndPosesY[:,0:2], pixelsAndPosesX[:,0:2], axis=0))

        self.pipette.set_max_speed(self.NORMAL_MAX_SPEED)
        self.pipette.wait_until_still()
        self.pipette.absolute_move_group(initPos, [0,1,2])
        self.pipette.wait_until_still()

        print('xmat', xmat)
        print('ymat', ymat)
        print('mat', mat)
        print('alt', alt)

        #find the starting point of the pipette (in pixels) for offset calculation
        xs = []
        ys = []
        for i in range(10):
            _, _, _, frame = self.camera._last_frame_queue[0]
            out = self.pipetteFinder.find_pipette(frame)
            if out != None:
                frame = cv2.circle(frame, out, 10, 0, 2)
                xs.append(out[0])
                ys.append(out[1])
        xs = np.array(xs)
        ys = np.array(ys)

        return alt, (np.median(xs), np.median(ys))
from holypipette.devices.manipulator import Manipulator, FakeManipulator
from holypipette.devices.pressurecontroller import PressureController
from .camera import Camera
import numpy as np
import cv2
from pathlib import Path
import time
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from enum import Enum

class PipetteState(Enum):
    TIP_NORMAL = 0
    TIP_BROKEN = 1
    TIP_SEALED = 2
    TIP_CLOGGED = 3
    TIP_BROKEN_IN = 4


class WorldModel():
    def __init__(self, pipette: Manipulator, pressure: PressureController, pixels_per_micron=1, pipette_img_size=[1016, 354]):
        self.pipette = pipette
        self.pressure = pressure
        self.pixels_per_micron = pixels_per_micron
        self.pipette_img_size = pipette_img_size

        # load cell annotations
        curFile = str(Path(__file__).parent.absolute())
        self.annotations = cv2.imread(curFile + "/FakeMicroscopeImgs/annotation.png", cv2.IMREAD_GRAYSCALE)
        self.pipette_state = PipetteState.TIP_NORMAL

        #setup pipette contants
        self._setupPipetteResistances()
        self.pipetteResistanceNoise = 0.1e6 #0.1 Mohm

        self.nearCellAddition = 0

        self.tau_range = [5 * 1e-3, 10 * 1e-3] #valid tau range
        self.tau = np.random.uniform(self.tau_range[0], self.tau_range[1])

        self.axis_resistance_range = [5 * 1e6, 30 * 1e6] #valid axis resistances between 5, 30 Mohm
        self.axis_resistance = np.random.uniform(self.axis_resistance_range[0], self.axis_resistance_range[1])

        self.seal_location = None
    
    def _setupPipetteResistances(self):
        self.normalResistance = np.random.randint(4e6, 7e6) #4-7 Mohm
        self.crashedResistance = np.random.randint(0.3e6, 2e6) #0.3-2 Mohm
        self.sealedResistance = np.random.randint(1e9, 2.5e9)
        self.brokenInResistance = np.random.randint(50e6, 250e6) #50-250 Mohm

    def isTipBroken(self):
        return self.pipette_state == PipetteState.TIP_BROKEN
        
    def isSealed(self):
        return self.pipette_state == PipetteState.TIP_SEALED
    
    def isBrokenIn(self):
        return self.pipette_state == PipetteState.TIP_BROKEN_IN
        
    def replacePipette(self):
        self._setupPipetteResistances() #new pipette, new resistances!
        self.pipette_state = PipetteState.TIP_NORMAL
        print('PIPETTE NORMAL!')
    
    def breakPipette(self):
        self.pipette_state = PipetteState.TIP_BROKEN
        print('PIPETTE BROKEN!')

    def cleanPipette(self):
        if self.pipette_state == PipetteState.TIP_CLOGGED:
            self.pipette_state = PipetteState.TIP_NORMAL
            print('PIPETTE CLEANED!')

    def getTau(self):
        return self.tau

    def getResistance(self):
        '''Get a simulated "steady-state" resistance for the pipette / system (in Ohms)
        '''
        res = self._standardPipetteResistance()

        if self.pipette_state == PipetteState.TIP_BROKEN or self.pipette_state == PipetteState.TIP_CLOGGED:
            return res
        
        pipettePos = self.pipette.position()
        distFromSlip = pipettePos[2]

        if self.pipette_state == PipetteState.TIP_SEALED or self.pipette_state == PipetteState.TIP_BROKEN_IN:
            seal_dist = np.linalg.norm(np.array(self.seal_location) - np.array(pipettePos))
            if distFromSlip > 20 or self.pressure.get_pressure() > 10 or seal_dist > 20:
                #moved too far away from the cell, lose seal
                self.pipette_state = PipetteState.TIP_CLOGGED
                print('PIPETTE CLOGGED!')
            
            if self.pressure.get_pressure() < -190 and self.pipette_state == PipetteState.TIP_SEALED:
                #break in
                self.pipette_state = PipetteState.TIP_BROKEN_IN
                print('BREAK IN!')

            return res

        if distFromSlip > 20 or 0 > distFromSlip:
            #we're not in the position range for patching (either broken or too far away)
            return res
        
        #add a bit of resistance if we're close to a cell
        if self.isCellAtPos((pipettePos[0], pipettePos[1])):
            res += 0.1e6 * (20 - distFromSlip)

            if self.pressure.get_pressure() <= 0 and random.random() < 0.01: #1% chance of gigaseal per frame
                #gigaseal!
                self.pipette_state = PipetteState.TIP_SEALED
                self.tau = np.random.uniform(self.tau_range[0], self.tau_range[1])
                self.axis_resistance = np.random.uniform(self.axis_resistance_range[0], self.axis_resistance_range[1])
                self.seal_location = pipettePos.copy()
                print('PIPETTE SEALED!')

        return res
    

    def getResistancePeak(self):
        '''Get a axis ("peak") resistance for the pipette / system (in Ohms)
        '''
        if self.pipette_state == PipetteState.TIP_BROKEN_IN:
            return self.axis_resistance
        elif self.pipette_state == PipetteState.TIP_SEALED:
            return self.getResistance() * 0.2
        else:
            return self.getResistance()
        
    def _standardPipetteResistance(self):
        '''The resistance of the pipette without any cells
        '''
        if self.isTipBroken():
            return self.crashedResistance + np.random.random() * self.pipetteResistanceNoise
        elif self.isSealed():
            return self.sealedResistance + np.random.random() * self.pipetteResistanceNoise
        elif self.isBrokenIn():
            return self.brokenInResistance + np.random.random() * self.pipetteResistanceNoise
        elif self.pipette_state == PipetteState.TIP_CLOGGED:
            return self.normalResistance * 1.25 + np.random.random() * self.pipetteResistanceNoise
        else:
            return self.normalResistance + np.random.random() * self.pipetteResistanceNoise


    def _isCellAtPos(self, x, y):

        #image indexing must be ints
        x = int(x)
        y = int(y)

        if self.annotations[y, x] > 0:
            return True
        else:
            return False
        
    def isCellAtPos(self, pipette_pos, screen_size=[1024, 1024]):

        #get pipette micron coords
        pipette_x = pipette_pos[0]
        pipette_y = pipette_pos[1]
        pipette_pos = np.array([pipette_x, pipette_y]) #already in stage coords because this sim uses identity matrix for stage_to_pipette

        #get pipette position in image coordinates
        pipette_pos_img_coords = pipette_pos * self.pixels_per_micron

        #get x,y - convert to int, make relative to frame
        pipette_img_x = int(pipette_pos_img_coords[0]) - self.annotations.shape[1] + screen_size[0] // 2
        pipette_img_y = int(pipette_pos_img_coords[1]) + screen_size[1] // 2

        #implement wrap around
        pipette_img_x = pipette_img_x % self.annotations.shape[1]
        pipette_img_y = pipette_img_y % self.annotations.shape[0]

        #account for negatives
        while pipette_img_x < 0:
            pipette_img_x = screen_size[1] + pipette_img_x 
        while pipette_img_y < 0:
            pipette_img_y = screen_size[0] + pipette_img_y

        return self._isCellAtPos(pipette_img_x, pipette_img_y)



class FakeCalCamera(Camera):
    def __init__(self, stageManip=None, pipetteManip=None, image_z=0, targetFramerate=40, worldModel=None):
        super(FakeCalCamera, self).__init__()
        self.width : int = 1024
        self.height : int = 1024
        self.exposure_time : int = 30
        self.stageManip : Manipulator = stageManip
        self.pipetteManip : Manipulator = pipetteManip
        self.worldModel : WorldModel = worldModel
        self.image_z : float = image_z
        self.pixels_per_micron : float = 1  # pixels / micrometers
        self.frameno : int = 0
        self.pipette = FakePipette(self.pipetteManip, self.pixels_per_micron, worldModel=self.worldModel)
        self.targetFramerate = targetFramerate

        curFile = str(Path(__file__).parent.absolute())

        #setup frame image (numpy because of easy rolling)
        self.frame = cv2.imread(curFile + "/FakeMicroscopeImgs/background.png", cv2.IMREAD_GRAYSCALE)
        self.frame = cv2.resize(self.frame, dsize=(self.width * 2, self.height * 2), interpolation=cv2.INTER_NEAREST)

        self.last_img = None
        self.last_stage_pos = None

        #creating large noise arrays slows down fps, create 100 arrays at startup instead
        self.noiseArrs = []
        for _ in range(100):
            self.noiseArrs.append((np.random.random((self.width, self.height)) * 30).astype(np.uint16))

        #start image recording thread
        self.start_acquisition()

    def normalize(self):
        print('normalize not implemented for FakeCalCamera')

    def set_exposure(self, value):
        if 0 < value <= 200:
            self.exposure_time = value

    def get_exposure(self):
        return self.exposure_time

    def get_microscope_image(self, x, y):
        if self.last_img is None or self.last_stage_pos[0] != x or self.last_stage_pos[1] != y:
            #we need to recalculate what the stage sees
            frame = np.roll(self.frame, int(y), axis=0)
            frame = np.roll(frame, int(x), axis=1)
            frame = frame[self.height//2:self.height//2+self.height,
                        self.width//2:self.width//2+self.width]
            
            #update cached frame
            self.last_stage_pos = [x, y]
            self.last_img = frame
        else:
            frame = self.last_img
            
        self.frameno += 1
        return Image.fromarray(frame)

    def get_16bit_image(self):
        #Note: use float 32 rather than int16 for opencv sobel filter compatability (focus score)
        return (self.raw_snap().astype(np.float32) / 255) * 65535 

    def get_frame_no(self):
        return self.frameno

    def raw_snap(self):
        '''
        Returns the current image.
        This is a blocking call (wait until next frame is available)
        '''
        start = time.time()
        # Use the part of the image under the microscope
        stage_x, stage_y, stage_z = self.stageManip.position_group([1, 2, 3])

        startPos = [0, 0, 0]
        stage_x = stage_x - startPos[0]
        stage_y = stage_y - startPos[1]
        stage_z = stage_z - startPos[2]

        #get background at current stage position
        img_x = -stage_x * self.pixels_per_micron
        img_y = -stage_y * self.pixels_per_micron
        frame = self.get_microscope_image(img_x, img_y)

        #blur cover slip proportionally to how far stage_z is from 0 (being focused in the img plane)
        focusFactor = abs(stage_z - self.image_z) / 10
        if focusFactor == 0:
            focusFactor = 0.1 #prevent division by zero

        frame = cv2.GaussianBlur(np.array(frame), (63,63), focusFactor)
        frame = Image.fromarray(frame)

        #add pipette to image
        frame = self.pipette.add_pipette_to_img(frame, [stage_x, stage_y, stage_z])

        #add noise, exposure
        exposure_factor = self.exposure_time/30.

        frame = frame + self.noiseArrs[self.frameno % len(self.noiseArrs)] #use pregenerated noise to increase fps
        frame[np.where(frame >= 255)] = 255
        frame[np.where(frame < 0)] = 0
        frame = frame.astype(np.uint8)

        dt = time.time() - start
        if dt < (1/self.targetFramerate):
            time.sleep((1/self.targetFramerate) - dt)

        # print(f'fps: {1/(time.time() - start)}')
        
        return frame
    
class FakePipette():

    def __init__(self, manipulator:Manipulator, microscope_pixels_per_micron, stage_to_pipette=np.eye(4,4), worldModel=None):

        stage_to_pipette = np.eye(4,4)
        self.rot_mat  = np.eye(4,4)

        stage_to_pipette = np.matmul(np.linalg.inv(self.rot_mat), stage_to_pipette)

        self.manipulator = manipulator
        self.pixels_per_micron = microscope_pixels_per_micron
        self.stage_to_pipette = stage_to_pipette #homoegeneous transform matrix from stage to pipette
        self.pipette_to_stage = np.linalg.inv(self.stage_to_pipette)
        self.worldModel:WorldModel = worldModel

        #setup pipette image (PIL b/c of easy pasting)
        curFile = str(Path(__file__).parent.absolute())
        self.pipetteImg = Image.open(curFile + "/FakeMicroscopeImgs/pipette.png").convert("L")
        self.pipetteImg, self.alphaMask = self._processPipetteImage(self.pipetteImg)
        self.pipetteImageBroken, self.alphaMaskBroken = self._processPipetteImage(Image.open(curFile + "/FakeMicroscopeImgs/pipette_crashed.png").convert("L"))

        
    
    def _processPipetteImage(self, image):
        image = image.resize((image.size[0] * 4, image.size[1] * 2), Image.Resampling.BILINEAR)
        filter = ImageEnhance.Brightness(image)
        image = filter.enhance(1.2)

        #create an alpha mask for the pipette (to make pipette see through)
        filter = ImageEnhance.Brightness(image)
        alphaMask = filter.enhance(1.2)
        return image, alphaMask

    def add_pipette_to_img(self, frame:Image, stagePos:list):

        # print(self.manipulator.position(), self.manipulator.raw_position())
        #get stage micron coords
        stage_x, stage_y, stage_z = stagePos

        #get stage pixel coords
        stage_img_x = stage_x * self.pixels_per_micron
        stage_img_y = stage_y * self.pixels_per_micron

        #get pipette micron coords
        pipette_x, pipette_y, pipette_z = self.manipulator.position()
        pipette_pos_h = np.array([pipette_x, pipette_y, pipette_z, 1])

        #get pipette position in stage coordinates
        pipette_pos_stage_coords_h = np.matmul(self.pipette_to_stage, pipette_pos_h.T)
        pipette_pos_stage_coords = pipette_pos_stage_coords_h[0:3] / pipette_pos_stage_coords_h[3]

        if not self.worldModel.isTipBroken() and pipette_pos_stage_coords[2] < 0:
            self.worldModel.breakPipette()

        #get pipette position in image coordinates
        pipette_pos_img_coords = pipette_pos_stage_coords * self.pixels_per_micron

        #get x,y - convert to int, make relative to frame
        pipette_img_x = int(pipette_pos_img_coords[0] - stage_img_x) - self.pipetteImg.size[0] #pipette_pos should correspond to tip of pipette (upper right) 
        pipette_img_y = int(pipette_pos_img_coords[1] - stage_img_y)

        #blur pipette proportionally to distance between stage_z and pipette_z
        focusFactor = abs(stage_z - pipette_pos_stage_coords[2]) / 10
        if focusFactor == 0:
            focusFactor = 0.1 #resolve divide by 0 error

        if self.worldModel.isTipBroken():
            pipetteImg = self.pipetteImageBroken
            alphaMask = self.alphaMaskBroken
        else:
            pipetteImg = self.pipetteImg
            alphaMask = self.alphaMask

        #blur img
        pipetteImg = cv2.GaussianBlur(np.array(pipetteImg), (63,63), focusFactor)
        pipetteImg = Image.fromarray(pipetteImg)

        #blur alpha channel
        alphaMask = cv2.GaussianBlur(np.array(alphaMask), (63,63), focusFactor / 2)
        alphaMask = alphaMask / 1.3
        alphaMask = Image.fromarray(alphaMask.astype(np.uint8))

        #add pipette to frame
        frame.paste(pipetteImg, (pipette_img_x, pipette_img_y), alphaMask)
        frame = np.array(frame) #convert back to numpy for opencv support
        return frame
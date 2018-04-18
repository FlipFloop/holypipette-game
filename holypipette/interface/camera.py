from __future__ import print_function
import numpy as np
from PyQt5 import QtCore, QtWidgets
import cv2

from holypipette.interface import TaskInterface, command


class CameraInterface(TaskInterface):
    updated_exposure = QtCore.pyqtSignal('QString', 'QString')

    def __init__(self, camera, with_tracking=False):
        super(CameraInterface, self).__init__()
        self.camera = camera
        self.with_tracking = with_tracking
        if with_tracking:
            self.multitracker = cv2.MultiTracker_create()
            self.movingList = []
        else:
            self.multitracker = None
            self.movingList = []

    def connect(self, main_gui):
        self.updated_exposure.connect(main_gui.set_status_message)
        self.signal_updated_exposure()
        if self.with_tracking:
            main_gui.image_edit_funcs.append(self.show_tracked_objects)

    def signal_updated_exposure(self):
        # Should be called by subclasses that actually support setting the exposure
        exposure = self.camera.get_exposure()
        if exposure > 0:
            self.updated_exposure.emit('Camera', 'Exposure: %.1fms' % exposure)

    @command(category='Camera',
             description='Increase exposure time by {:.1f}ms',
             default_arg=2.5)
    def increase_exposure(self, increase):
        self.camera.change_exposure(2.5)
        self.signal_updated_exposure()

    @command(category='Camera',
             description='Increase exposure time by {:.1f}ms',
             default_arg=2.5)
    def decrease_exposure(self, increase):
        self.camera.change_exposure(-2.5)
        self.signal_updated_exposure()

    @command(category='Camera',
             description='Save the current image to a file')
    def save_image(self):
        try:
            import imageio
        except ImportError:
            print('Saving images needs imageio')
            return
        frame = self.camera.snap()
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(caption='Save image',
                                                         filter='Images (*.png, *.tiff)')
        if len(fname):
            imageio.imwrite(fname, frame)

    def show_tracked_objects(self, img):
        from holypipette.gui.movingList import moveList
        moveList.clear()
        ok, boxes = self.multitracker.update(img)
        for newbox in boxes:
            p1 = (int(newbox[0]), int(newbox[1]))
            p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))
            cv2.rectangle(img, p1, p2, (255, 255, 255), 2)
            x = int(newbox[0] + 0.5 * newbox[2])
            y = int(newbox[1] + 0.5 * newbox[3])
            xs = x - self.camera.width / 2
            ys = y - self.camera.height / 2
            moveList.append(np.array([xs, ys]))

        return img

    @command(category='Camera',
             description='Select an object for automatic tracking')
    def track_object(self, position=None):
        # the position argument is only used when the action is triggered by a
        # mouse click -- we just ignore it
        img = self.camera.snap()
        cv2.namedWindow('target cell selection', cv2.WINDOW_AUTOSIZE)
        while True:
            cv2.imshow('target cell selection', img)
            bbox1 = cv2.selectROI('target cell selection', img)
            self.multitracker.add(cv2.TrackerKCF_create(), img, bbox1)
            cv2.destroyWindow('target cell selection')
            break

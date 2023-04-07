import logging

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5 import QtCore

from pyqtgraph import PlotWidget, plot

import threading
import time

import numpy as np
from collections import deque
from holypipette.devices.amplifier import DAQ
from holypipette.devices.pressurecontroller import PressureController

__all__ = ["EPhysGraph"]

class EPhysGraph(QWidget):
    """A window that plots electrophysiology data from the DAQ
    """
    
    def __init__(self, daq : DAQ, pressureController : PressureController, parent=None):
        super().__init__()

        #stop matplotlib font warnings
        logging.getLogger('matplotlib.font_manager').disabled = True

        self.daq = daq
        self.pressureController = pressureController

        #constants for Multi Clamp
        self.externalCommandSensitivity = 20 #mv/V
        self.triggerLevel = 0.1 #V

        #setup window
        self.setWindowTitle("Electrophysiology")

        self.squareWavePlot = PlotWidget()
        self.pressurePlot = PlotWidget()

        #set background color of plots
        self.squareWavePlot.setBackground('w')
        self.pressurePlot.setBackground('w')

        #set axis colors to black
        self.squareWavePlot.getAxis('left').setPen('k')
        self.squareWavePlot.getAxis('bottom').setPen('k')
        self.pressurePlot.getAxis('left').setPen('k')
        self.pressurePlot.getAxis('bottom').setPen('k')

        #set labels
        self.squareWavePlot.setLabel('left', "Voltage", units='V')
        self.squareWavePlot.setLabel('bottom', "Time", units='s')
        self.pressurePlot.setLabel('left', "Pressure", units='mbar')
        self.pressurePlot.setLabel('bottom', "Time", units='s')

        self.pressureData = deque(maxlen=100)

        #create a quarter layout for 4 graphs
        layout = QVBoxLayout()
        layout.addWidget(self.squareWavePlot)
        layout.addWidget(self.pressurePlot)

        self.setLayout(layout)
        
        self.updateTimer = QtCore.QTimer()
        self.updateDt = 100 #ms
        self.updateTimer.timeout.connect(self.update_plot)
        self.updateTimer.start(self.updateDt)

        #start async daq data update
        self.lastestDaqData = None
        self.daqUpdateThread = threading.Thread(target=self.updateDAQDataAsync, daemon=True)
        self.daqUpdateThread.start()

        #show window and bring to front
        self.raise_()
        self.show()

    def updateDAQDataAsync(self):
        while True:
            raw_data = self.daq.getDataFromSquareWave(10, 5000, 0.5, 0.1, 0.5)
            mean = np.mean(raw_data[1, :])
            #split array into greater than and less than mean
            low_values = raw_data[:, raw_data[1, :] < mean]
            high_values = raw_data[:, raw_data[1, :] > mean]

            low_mean = np.mean(low_values[1, :])
            high_mean = np.mean(high_values[1, :])

            # set low to mean 0
            raw_data[1, :] -= low_mean
            triggerSpots = np.where(raw_data[1, :] > self.triggerLevel)[0]
            lowSpots = np.where(raw_data[1, :] < 0)[0]

            #find first rising edge (first low to high transition)
            if len(lowSpots) == 0 or len(triggerSpots) == 0:
                print("no rising edge found")
                self.lastestDaqData = raw_data
                continue

            try:
                # get rising edge location (first trigger spot after first low spot)
                rising_edge = triggerSpots[triggerSpots > lowSpots[0]][0]
                falling_edge = lowSpots[lowSpots > rising_edge][0]
                second_rising_edge = triggerSpots[triggerSpots > falling_edge][0]

                # trim data to rising edge
                squarewave = raw_data[:, rising_edge:second_rising_edge]

                self.lastestDaqData = squarewave
            except:
                print("no rising edge found")
                self.lastestDaqData = raw_data
            time.sleep(0.1)

    def update_plot(self):
        #update data
        if self.lastestDaqData is not None:
            self.squareWavePlot.clear()
            self.squareWavePlot.plot(self.lastestDaqData[0], self.lastestDaqData[1])
            self.lastestDaqData = None
        
        self.pressureData.append(self.pressureController.measure())
        pressureX = [i * self.updateDt / 1000 for i in range(len(self.pressureData))]
        self.pressurePlot.clear()
        self.pressurePlot.plot(pressureX, self.pressureData, pen='k')
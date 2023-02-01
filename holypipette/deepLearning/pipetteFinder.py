import cv2
import numpy as np
import time
from pathlib import Path

class PipetteFinder():

	def __init__(self):
		curFile = str(Path(__file__).parent.absolute())
		self.yoloNet = cv2.dnn.readNetFromONNX(curFile + '/pipetteModel/pipette-nano.onnx')

		layer_names = self.yoloNet.getLayerNames()
		self.output_layers = [layer_names[i-1] for i in self.yoloNet.getUnconnectedOutLayers()]

		self.pipette_class = 0

	def find_pipette(self, img):
		''' return the x and y position (in pixels) of the pipette in the given image using a YOLO object detection model
			or None if there is no detected pipette in the image
		'''

		if len(img.shape) == 2:
			#neural net expects color image, convert to color
			img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

		height, width, _ = img.shape #color image

		#run the image through the model
		blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (640, 640), swapRB=True, crop=False)
		self.yoloNet.setInput(blob)
		outs = self.yoloNet.forward(self.output_layers)

		confidences = []
		boxes = []
		for out in outs:
			for detection in out:
				idx = np.argmax(detection[4, :])
				detection = detection[:, idx]
				x, y, width, height, objectness = tuple(detection)
				if objectness < 0.20:
					continue

				center_x = x
				center_y = y
				boxes.append([center_x, center_y])
				confidences.append(float(objectness))

		if len(boxes) == 0:
			return None #no pipette detected
		
		confidences = np.array(confidences)
		best_x, best_y = boxes[confidences.argmax()]

		#model outputs pos for a 640x640 img.  rescale x,y to input image size
		best_x = (best_x / 640) * img.shape[1]
		best_y = (best_y / 640) * img.shape[0]

		#convert to int (for opencv drawing functions)
		best_x = int(best_x)
		best_y = int(best_y)

		return best_x, best_y
	
if __name__ == '__main__':
	finder = PipetteFinder()
	img = cv2.imread('/home/nathan/Desktop/82.png')

	#find pipette, draw location to img
	start = time.time()
	x,y = finder.find_pipette(img)

	print(f'framerate: {1 / (time.time() - start)}')
	cv2.circle(img, (x,y), 3, (0, 255, 0))

	#show img
	cv2.imshow("pipette finding test", img)
	cv2.waitKey(0)


		

				
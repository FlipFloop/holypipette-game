"""
Search a template image in an other image
Not scale nor rotation invariant

Uses OpenCV.
Alternatively, one might use skimage.feature.match_template
"""

import cv2

__all__ = ['templatematching','MatchingError']

class MatchingError(Exception):
    def __init__(self, value):
        self.value # best matching value

    def __str__(self):
        return 'The template was not found'

def templatematching(img, template):
    """
    Search a template image in an other image
    Not scale nor rotation invariant.

    Parameters
    ----------
    img : image to look in
    template : image to look for

    Returns
    -------
    maxloc: location (x,y) in the image of maxval
    maxval: maximum value corresponding to the best matching ratio
    """

    # Searching for a template match using cv2.TM_COEFF_NORMED detection
    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    # Getting maxval and maxloc
    _, maxval, _, maxloc = cv2.minMaxLoc(res)

    # Threshold for maxval to ensure a good template matching
    threshold = 0.75

    if maxval >= threshold:
        raise MatchingError(maxval)

    return maxloc, maxval


if __name__ == '__main__':
    img = cv2.imread('pipette.jpg', 0)
    template = cv2.imread('template.jpg', 0)
    res, val, loc = templatematching(img, template)
    x, y = loc[:2]
    if res:
        h = template.shape[1]
        w = template.shape[0]
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255))
    cv2.imshow("camera", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

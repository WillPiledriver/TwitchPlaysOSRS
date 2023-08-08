import sys
from pyclick import HumanClicker, HumanCurve
import pyautogui
import math

if len(sys.argv) >= 5:
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    duration = float(sys.argv[3])
    button = str(sys.argv[4])
    steady = bool(int(sys.argv[5])) if len(sys.argv) >= 6 else False

    # initialize HumanClicker object
    hc = HumanClicker()

    if steady:
        # Create a HumanCurve object with reduced randomness
        pos = pyautogui.position()
        distance = math.sqrt((x - pos[0])**2 + (y - pos[1])**2)
        hc.move((x, y), duration, humanCurve=HumanCurve(pos, (x, y), distortionStdev=0.1, distortionMean=0.1, distortionFrequency=0.1, targetPoints=min(100, max(int(distance / 2), 2)), offsetBoundaryX=5, offsetBoundaryY=5))
    else:
        # move the mouse to position (x, y) on the screen in the specified duration with default randomness
        hc.move((x, y), duration)

    # mouse click
    hc.click(button=button)
else:
    print("Insufficient arguments provided.")

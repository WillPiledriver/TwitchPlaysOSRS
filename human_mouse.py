import sys
from pyclick import HumanClicker

if len(sys.argv) >= 4:
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    duration = float(sys.argv[3])
    button = str(sys.argv[4])

    # initialize HumanClicker object
    hc = HumanClicker()
    # move the mouse to position (x, y) on the screen in the specified duration
    hc.move((x, y), duration)
    # mouse click
    hc.click(button=button)
else:
    print("Insufficient arguments provided.")
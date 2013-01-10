import sys, os

self = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if self not in sys.path:
    sys.path.insert(0, self)

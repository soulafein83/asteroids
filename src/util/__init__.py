import os

# Repository root and assets folder, resolved relative to THIS FILE so the
# game works no matter which directory it is launched from.
# __file__ is at <root>/src/util/__init__.py, so three dirnames up is <root>.
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES_DIR = os.path.join(BASE_DIR, "res")
FONT_PATH = os.path.join(RES_DIR, "Hyperspace.otf")

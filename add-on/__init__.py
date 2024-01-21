from aqt import mw
from aqt.utils import showInfo
from .main import main_function
import sys
import os

# Assuming 'lib' is in the same directory as your script
lib_path = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.insert(0, lib_path)
import openai

print(openai.__version__)


def add_menu_item():
    action = mw.form.menuTools.addAction("Kobo to Anki")
    action.triggered.connect(main_function)

add_menu_item()

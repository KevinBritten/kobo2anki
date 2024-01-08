from aqt import mw
from aqt.utils import showInfo
from .main import main_function

def add_menu_item():
    action = mw.form.menuTools.addAction("Kobo to Anki")
    action.triggered.connect(main_function)

add_menu_item()

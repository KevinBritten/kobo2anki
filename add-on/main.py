# main.py
from aqt import mw
from .utils import extract_words_from_kobo, create_anki_cards, show_confirmation_dialog

def main_function():
    # Step 1: Extract words from Kobo
    words = extract_words_from_kobo()

    # Step 2: Show confirmation dialog
    show_confirmation_dialog(words)

# Your Anki menu action setup can go here

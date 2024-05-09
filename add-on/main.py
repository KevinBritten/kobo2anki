# main.py
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from .utils import extract_words_from_kobo, create_anki_cards, show_confirmation_dialog,extract_words_and_context

def main_function():
    open_main_menu()

def translate_words():
    # # Step 1: Extract words from Kobo
    
    # words = extract_words_from_kobo()

    # # Step 2: Show confirmation dialog
    # show_confirmation_dialog(words)
    
    annotations = extract_words_and_context()
    print(annotations)

# Your Anki menu action setup can go here

from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

def open_options():
    dialog = QDialog(mw)
    dialog.setWindowTitle("Options")
    
    layout = QVBoxLayout(dialog)
    
    # Create a combo box to list decks
    combo_decks = QComboBox()
    decks = mw.col.decks.all_names_and_ids()
    for deck in decks:
        combo_decks.addItem(deck.name, deck.id)
    
    # Load the currently selected deck ID from config
    config = mw.addonManager.getConfig(__name__)
    selected_deck_id = config.get('selected_deck_id', None)
    if selected_deck_id:
        index = combo_decks.findData(selected_deck_id)
        if index >= 0:
            combo_decks.setCurrentIndex(index)
    
    layout.addWidget(combo_decks)

    # Create checkbox for enabling word deletion
    checkbox_delete_words = QCheckBox("Enable Word Deletion")
    enable_word_deletion = config.get('enable_word_deletion', False)
    checkbox_delete_words.setChecked(enable_word_deletion)
    layout.addWidget(checkbox_delete_words)
    
    checkbox_delete_annotation = QCheckBox("Enable Annotation Deletion")
    enable_annotation_deletion = config.get('enable_annotation_deletion', False)
    checkbox_delete_annotation.setChecked(enable_annotation_deletion)
    layout.addWidget(checkbox_delete_annotation)
    
    save_cancel_layout = QHBoxLayout()
    btn_save = QPushButton("Save")
    btn_cancel = QPushButton("Cancel")
    def save_selection():
        # Save the selected deck ID to config
        selected_index = combo_decks.currentIndex()
        selected_id = combo_decks.itemData(selected_index)
        config['selected_deck_id'] = selected_id

        # Save the state of the checkbox to config
        config['enable_word_deletion'] = checkbox_delete_words.isChecked()
        config['enable_annotation_deletion'] = checkbox_delete_annotation.isChecked()
        mw.addonManager.writeConfig(__name__, config)
        dialog.accept()
    
    
    btn_save.clicked.connect(save_selection)
    btn_cancel.clicked.connect(dialog.reject)
    save_cancel_layout.addWidget(btn_save)
    save_cancel_layout.addWidget(btn_cancel)
    layout.addLayout(save_cancel_layout)
    
    dialog.setLayout(layout)
    dialog.exec()

def open_main_menu():
    # Create a QDialog
    dialog = QDialog(mw)
    dialog.setWindowTitle("Main Menu")
    
    # Layout for buttons
    layout = QVBoxLayout()
    
    # Button for translating words
    btn_translate = QPushButton("Translate Words")
    btn_translate.clicked.connect(translate_words)  # Connect button to function
    layout.addWidget(btn_translate)
    
    # Button for opening options
    btn_options = QPushButton("Options")
    btn_options.clicked.connect(open_options)  # Connect button to function
    layout.addWidget(btn_options)
    
    # Set layout on QDialog
    dialog.setLayout(layout)
    
    # Show the dialog
    dialog.exec()

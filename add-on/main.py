# main.py
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from .utils import update_config, show_confirmation_dialog,extract_words_and_context, get_available_languages
import threading

import os
import xml.etree.ElementTree as ET

main_menu_dialog = None

selected_books = True
source_langs = ['loading languages']
target_langs = ['loading languages']

def main_function():
    global selected_books
    threading.Thread(target=set_lang_options).start()
    open_main_menu()
 


def translate_words():
    annotations = extract_words_and_context(selected_books)
    if annotations:
        show_confirmation_dialog(annotations, main_menu_dialog)
    elif annotations is not None:
        QMessageBox.warning(None, "No Annotations Found", "No annotations were found.")



from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

def open_options():
    dialog = QDialog(mw)
    dialog.setWindowTitle("Options")
    
    layout = QVBoxLayout(dialog)
    
    # Create a combo box to list decks
    combo_decks_label = QLabel("Select a deck")
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
    layout.addWidget(combo_decks_label)
    layout.addWidget(combo_decks)
    
    # Source language
    source_lang_label = QLabel("Source Language")
    source_lang_entry = QComboBox()
    source_lang_entry.addItems(source_langs)
    source_lang_entry.setCurrentText(config.get('source_lang', 'FR'))
    layout.addWidget(source_lang_label)
    layout.addWidget(source_lang_entry)

    # Target language
    target_lang_label = QLabel("Target Language")
    target_lang_entry = QComboBox()
    target_lang_entry.addItems(target_langs)
    target_lang_entry.setCurrentText(config.get('target_lang', 'EN-GB'))
    layout.addWidget(target_lang_label)
    layout.addWidget(target_lang_entry)

    
    dir_label = QLabel("Select Directory")
    dir_entry = QLineEdit()
    dir_entry.setText(config.get('annotation-directory', ''))
    layout.addWidget(dir_label)
    layout.addWidget(dir_entry)

    def choose_directory():
        dir_path = QFileDialog.getExistingDirectory(dialog, "Select Directory")
        if dir_path:
            dir_entry.setText(dir_path)
    
    btn_choose_dir = QPushButton("Choose Directory")
    btn_choose_dir.clicked.connect(choose_directory)
    layout.addWidget(btn_choose_dir)
    
    checkbox_skip_annotations_with_existing_card = QCheckBox("Enable skip_annotations_with_existing_card")
    enable_skip_annotations_with_existing_card = config.get('skip_annotations_with_existing_card', False)
    checkbox_skip_annotations_with_existing_card.setChecked(enable_skip_annotations_with_existing_card)
    layout.addWidget(checkbox_skip_annotations_with_existing_card)

    checkbox_add_empty_annotations = QCheckBox("Enable add_empty_annotations")
    enable_add_empty_annotations = config.get('add_empty_annotations', False)
    checkbox_add_empty_annotations.setChecked(enable_add_empty_annotations)
    layout.addWidget(checkbox_add_empty_annotations)
    
    checkbox_add_single_word_empty_annotations_only = QCheckBox("Enable add_single_word_empty_annotations_only")
    enable_add_single_word_empty_annotations_only = config.get('add_single_word_empty_annotations_only', True)
    checkbox_add_single_word_empty_annotations_only.setChecked(enable_add_single_word_empty_annotations_only)
    layout.addWidget(checkbox_add_single_word_empty_annotations_only)
    
    save_cancel_layout = QHBoxLayout()
    btn_save = QPushButton("Save")
    btn_cancel = QPushButton("Cancel")
    def save_selection():
        # Save the selected deck ID to config
        selected_index = combo_decks.currentIndex()
        selected_id = combo_decks.itemData(selected_index)
        config['selected_deck_id'] = selected_id
        
        config['annotation-directory'] = dir_entry.text()
        
        config['source_lang'] = source_lang_entry.currentText()
        config['target_lang'] = target_lang_entry.currentText()

        # Save the state of the checkbox to config
        config['skip_annotations_with_existing_card'] = checkbox_skip_annotations_with_existing_card.isChecked()
        config['add_empty_annotations'] = checkbox_add_empty_annotations.isChecked()
        config['add_single_word_empty_annotations_only'] = checkbox_add_single_word_empty_annotations_only.isChecked()
        mw.addonManager.writeConfig(__name__, config)
        update_config()
        dialog.accept()
    
    
    btn_save.clicked.connect(save_selection)
    btn_cancel.clicked.connect(dialog.reject)
    save_cancel_layout.addWidget(btn_save)
    save_cancel_layout.addWidget(btn_cancel)
    layout.addLayout(save_cancel_layout)
    
    dialog.setLayout(layout)
    dialog.exec()
    
def open_select_books():
    config = mw.addonManager.getConfig(__name__)
    folder_path = config.get('annotation-directory', '')
    namespaces = {'ns': 'http://ns.adobe.com/digitaleditions/annotations', 'dc': 'http://purl.org/dc/elements/1.1/'}
    books = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".annot"):
            file_path = os.path.join(folder_path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()
            book_title_element = root.find(".//ns:publication/dc:title", namespaces)
            if book_title_element is not None:
                book_title = book_title_element.text
                books.append(book_title)

    # Create a new window with checkboxes for each book title
    dialog = QDialog(mw)
    dialog.setWindowTitle("Select Books")
    layout = QVBoxLayout()
    global selected_books
    
    checkboxes = []
    for book in books:
        checkbox = QCheckBox(book)
        if ((selected_books is True) or book in selected_books) :
            checkbox.setChecked(True)  # Set checkbox to be checked by default
        layout.addWidget(checkbox)
        checkboxes.append(checkbox)
    
        # Add Select All and Select None buttons
    btn_select_all = QPushButton("Select All")
    btn_select_none = QPushButton("Select None")
    
    def select_all():
        for checkbox in checkboxes:
            checkbox.setChecked(True)
    
    def select_none():
        for checkbox in checkboxes:
            checkbox.setChecked(False)
            
    btn_select_all.clicked.connect(select_all)
    btn_select_none.clicked.connect(select_none)

    layout.addWidget(btn_select_all)
    layout.addWidget(btn_select_none)


    
    # Add OK and Cancel buttons
    button_box = QHBoxLayout()
    btn_ok = QPushButton("OK")
    btn_cancel = QPushButton("Cancel")
    btn_ok.clicked.connect(dialog.accept)
    btn_cancel.clicked.connect(dialog.reject)
    button_box.addWidget(btn_ok)
    button_box.addWidget(btn_cancel)
    layout.addLayout(button_box)

    dialog.setLayout(layout)
    if dialog.exec():
        selected_books = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]

def open_main_menu():
    global main_menu_dialog
    # Create a QDialog
    main_menu_dialog = QDialog(mw)
    main_menu_dialog.setWindowTitle("Main Menu")
    
    # Layout for buttons
    layout = QVBoxLayout()
    
    # Button for translating words
    btn_translate = QPushButton("Translate Words")
    btn_translate.clicked.connect(translate_words)  # Connect button to function
    layout.addWidget(btn_translate)
    
     # Button for opening menu to select books
    btn_select_books = QPushButton("Select Books")
    btn_select_books.clicked.connect(open_select_books)  # Connect button to function
    layout.addWidget(btn_select_books)
    
    # Button for opening options
    btn_options = QPushButton("Options")
    btn_options.clicked.connect(open_options)  # Connect button to function
    layout.addWidget(btn_options)
    
    # Set layout on QDialog
    main_menu_dialog.setLayout(layout)
    
    # Show the dialog
    main_menu_dialog.exec()
    
def set_lang_options():
    global target_langs
    global source_langs
    target_langs = get_available_languages('target')
    source_langs = get_available_languages('source')

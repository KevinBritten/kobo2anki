# main.py
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from .utils import update_config, show_confirmation_dialog,extract_words_and_context

main_menu_dialog = None

def main_function():
    open_main_menu()

def translate_words():
    annotations = extract_words_and_context()
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
    
    source_lang_label = QLabel("Source Language")
    source_lang_entry = QLineEdit()
    source_lang_entry.setText(config.get('source_lang', 'FR'))
    layout.addWidget(source_lang_label)
    layout.addWidget(source_lang_entry)
    
    target_lang_label = QLabel("Target Language")
    target_lang_entry = QLineEdit()
    target_lang_entry.setText(config.get('target_lang', 'EN-GB'))
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
        
        config['source_lang'] = source_lang_entry.text()
        config['target_lang'] = target_lang_entry.text()

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
    
    # Button for opening options
    btn_options = QPushButton("Options")
    btn_options.clicked.connect(open_options)  # Connect button to function
    layout.addWidget(btn_options)
    
    # Set layout on QDialog
    main_menu_dialog.setLayout(layout)
    
    # Show the dialog
    main_menu_dialog.exec()

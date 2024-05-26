# utils.py
import sqlite3
import traceback
from anki.notes import Note
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

lib_path = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.insert(0, lib_path)
config = mw.addonManager.getConfig(__name__)

def update_config():
    global config
    config = mw.addonManager.getConfig(__name__)



def define_with_deepl(word, context):
    import deepl
    api_key = config.get("deepl_api_key", "")
    translator = deepl.Translator(api_key)
    source_lang = config.get("source_lang", "FR")
    target_lang = config.get("target_lang", "EN-GB")
    
    try:
        translation = translator.translate_text(word, context=context, source_lang=source_lang, target_lang=target_lang, glossary=None) 
        return translation.text  # or some manipulation if you want to extract the translation of 'word' specifically
        
    except Exception as e:
        print("Error in translating with DeepL:", str(e))
        return None


def define_with_open_ai(word, context):
    from openai import OpenAI
    client = OpenAI(
        api_key=config.get("openai_api_key", ""),
    )
    prompt = f'Translate "{word}" to english. Do not include any text outside of the definition in your response. If there are multiple definitions, use the following sentence for context (Do not repeat the word or the sentence, only output the definition): {context}'
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
        )
    definition = response.choices[0].message.content
    return definition

def get_definition_func():
    api_mode = config.get("api_mode", "deepl")  # Default to "deepl" if not specified
    if api_mode == "openai":
        definition_func = define_with_open_ai
    elif api_mode == "deepl":
        definition_func = define_with_deepl
    else:
        raise ValueError("Invalid api_mode in config")
    return definition_func

def create_anki_cards(annotations):
    # Load the deck ID from the configuration
    definition_func = get_definition_func()
    deck_id = config.get('selected_deck_id')
    successful_identifiers = []
    for annotation in annotations:
        word = annotation['word']
        annotation_text = annotation['annotation_text']
        identifier = annotation['identifier']
        definition = definition_func(word,annotation_text)
        modelID = None  # Initialize modelID to None
        models = mw.col.models.all()  # Retrieve all models in the collection
        for model in models:
            if model['name'] == "Basic":  # Check if the model name is "Basic"
                modelID = model['id']  # Store the model ID in modelID
                break  # Exit the loop once the desired model is found
        # Create a new note
        note = mw.col.new_note(modelID)  # Include the reference to the Anki collection
        # Set the word as the front of the card
        note["Back"] = word + ' - ' + definition
        note["Front"] = annotation_text
        if mw.col.add_note(note, deck_id):
             successful_identifiers.append(identifier)
    mw.reset()
    return successful_identifiers

def add_checked_elements(successful_identifiers):
    script_dir = os.path.dirname(__file__)
    folder_path = os.path.join(script_dir, 'test-data', 'Digital Editions')
    # Define namespaces
    namespaces = {'ns': 'http://ns.adobe.com/digitaleditions/annotations', 'dc': 'http://purl.org/dc/elements/1.1/'}

    for filename in os.listdir(folder_path):
        if filename.endswith(".annot"):
            file_path = os.path.join(folder_path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Iterate over annotations
            for parent_elem in root.findall(".//ns:annotation", namespaces):
                identifier_elem = parent_elem.find('.//dc:identifier', namespaces)
                if identifier_elem is not None and identifier_elem.text in successful_identifiers:
                    checked_elem = parent_elem.find(".//checked")
                    if checked_elem is None:
                        checked_elem = ET.Element('checked')
                        checked_elem.text = 'true'
                        parent_elem.insert(0, checked_elem)

            # Save the modified file
            tree.write(file_path)


def show_confirmation_dialog(annotations,main_menu_dialog):
    dialog = QDialog(mw)
    dialog.setWindowTitle("Confirmation")
    dialog.setGeometry(100, 100, 300, 150)
    layout = QVBoxLayout(dialog)

    label = QLabel("Do you want to create Anki cards for the following words?")
    layout.addWidget(label)

    for annotation in annotations:
        word = annotation['word']
        label = QLabel(str(word))
        layout.addWidget(label)

    def on_confirm():
        # Call the function that creates the cards and get the number of cards added
        successful_identifiers = create_anki_cards(annotations)
        if config.get("add_checked_element_to_annotations", True):
            add_checked_elements(successful_identifiers)
        # Display a message box with the number of cards added
        QMessageBox.information(dialog, "Cards Added", f"{len(successful_identifiers)} cards added")
        
        # Close the original dialog
        dialog.close()
        main_menu_dialog.accept()

    confirm_button = QPushButton("Confirm")
    confirm_button.clicked.connect(on_confirm)
    layout.addWidget(confirm_button)

    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.close)
    layout.addWidget(cancel_button)

    dialog.exec()

def extract_words_and_context():
    script_dir = os.path.dirname(__file__)
    folder_path = os.path.join(script_dir, 'test-data', 'Digital Editions')
    annotations = []
    # Define namespaces
    namespaces = {'ns': 'http://ns.adobe.com/digitaleditions/annotations', 'dc': 'http://purl.org/dc/elements/1.1/'}

    for filename in os.listdir(folder_path):
        if filename.endswith(".annot"):
            file_path = os.path.join(folder_path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            #Load config settings
            skip_annotations_with_checked_element = config.get("skip_annotations_with_checked_element", True)
            add_empty_annotations = config.get("add_empty_annotations", False)
            add_single_word_empty_annotations_only = config.get("add_single_word_empty_annotations_only", True)
            # Iterate over annotations
            for parent_elem in root.findall(".//ns:annotation", namespaces):
                checked_elem = parent_elem.find(".//checked")
                if checked_elem is None or (checked_elem is not None and not skip_annotations_with_checked_element):
                    # Find the text element under fragment
                    annotation_elem = parent_elem.find(".//ns:target/ns:fragment/ns:text", namespaces)
                    annotation_text = annotation_elem.text if annotation_elem is not None else None                
                    word_elem = parent_elem.find(".//ns:content/ns:text", namespaces)
                    word_elem_content = word_elem.text if word_elem is not None else None 
                    identifier = parent_elem.find('.//dc:identifier', namespaces).text
                    word_text = ""
                    if word_elem_content is not None or add_empty_annotations:
                        if word_elem_content is None:
                            #check for whitespace in annotation_text
                            contains_whitespace = any(char.isspace() for char in annotation_text)
                            if add_single_word_empty_annotations_only and contains_whitespace:
                                continue
                            word_text = annotation_text
                        elif word_elem_content.isdigit():
                            # Case 1: word_elem_content is a single number
                            words = annotation_text.split()
                            index = int(word_elem_content) - 1
                            if 0 <= index < len(words):
                                word_text = words[index]
                        elif '.' in word_elem_content and all(part.isdigit() for part in word_elem_content.split('.')):
                            # Case 2: word_elem_content is of format "num1.num2"
                            start_index, end_index = map(int, word_elem_content.split('.'))
                            words = annotation_text.split()
                            if 0 <= start_index-1 < len(words) and 0 < end_index <= len(words) and start_index <= end_index:
                                word_text = ' '.join(words[start_index-1:end_index])
                        else:
                            # Case 3: word_elem_content is a string in any other format
                            word_text = word_elem_content
                    if annotation_text is not None and word_text:
                        annotations.append({'annotation_text': annotation_text, 'word': word_text, 'identifier':identifier})
           
    return annotations

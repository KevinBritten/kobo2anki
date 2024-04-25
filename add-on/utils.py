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


def define_with_deepl(word, context):
    import deepl

    api_key = config.get("deepl_api_key", "")
    translator = deepl.Translator(api_key)
    source_lang = "FR"  # French
    target_lang = "EN-GB"  # English
    
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

api_mode = config.get("api_mode", "deepl")  # Default to "deepl" if not specified

if api_mode == "openai":
    definition_func = define_with_open_ai
elif api_mode == "deepl":
    definition_func = define_with_deepl
else:
    raise ValueError("Invalid api_mode in config")

def extract_words_from_kobo():
    script_dir = os.path.dirname(__file__)
    db_path = os.path.join(script_dir, 'test-data', 'KoboReader.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT Text, DateCreated FROM WordList"
    cursor.execute(query)
    words = cursor.fetchall()
    conn.close()
    return words

def get_annotations(folder_path):
    annotations = {}
    # Define namespaces
    namespaces = {'ns': 'http://ns.adobe.com/digitaleditions/annotations', 'dc': 'http://purl.org/dc/elements/1.1/'}

    for filename in os.listdir(folder_path):
        if filename.endswith(".annot"):
            file_path = os.path.join(folder_path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Iterate over annotations
            for annotation_elem in root.findall(".//ns:annotation", namespaces):
                identifier = annotation_elem.find(".//dc:identifier", namespaces).text
                date_str = annotation_elem.find(".//dc:date", namespaces).text
                date = parse_date(date_str)
                # Find the text element under fragment
                text_elem = annotation_elem.find(".//ns:target/ns:fragment/ns:text", namespaces)
                text = text_elem.text if text_elem is not None else None                
                # Add to annotations dictionary
                annotations[identifier] = {'text': text, 'timestamp': date}

    return annotations

def match_annotations_and_words(words, annotations):
    pairs = []
    for word, DateCreated in words:
        matching_annotation = ""
        date = parse_date(DateCreated)
        for annotation in annotations.values():
            if annotation['timestamp'] > date:
                if word in annotation['text']:
                    matching_annotation = annotation['text']
                break  # Stop searching after finding the first matching annotation
        pairs.append({'word': word, 'matching_annotation': matching_annotation})
    return pairs

def create_anki_cards(pairs):
    deck_name = "Test"
    # Get the default deck ID as an integer
    deck_id = mw.col.decks.id(deck_name)
    successful_words = []    
    # Iterate through the words and create Anki cards
    for pair in pairs:
        word = pair['word']
        matching_annotation = pair['matching_annotation']
        definition = definition_func(word,matching_annotation)
        
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
        note["Front"] = matching_annotation
      
        if mw.col.add_note(note, deck_id):
            successful_words.append(word)
    if config.get("enable_word_deletion", False):
        delete_successful_words(successful_words)
    mw.reset()
    return successful_words.__len__()
    
def delete_successful_words(words):
    # Connect to the SQLite database
    script_dir = os.path.dirname(__file__)
    db_path = os.path.join(script_dir, 'test-data', 'KoboReader.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Prepare the SQL delete query
        # Use parameter substitution to safely insert the words into the query
        query = "DELETE FROM WordList WHERE Text IN ({})".format(','.join('?' * len(words)))
        
        # Execute the query with the list of words
        cursor.execute(query, words)
        
        # Commit the changes
        conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()


def parse_date(date_str):

    date_str_no_z = date_str[:-1]
    date = datetime.fromisoformat(date_str_no_z)
    return date




def show_confirmation_dialog(words):
    dialog = QDialog(mw)
    dialog.setWindowTitle("Confirmation")
    dialog.setGeometry(100, 100, 300, 150)
    layout = QVBoxLayout(dialog)

    label = QLabel("Do you want to create Anki cards for the following words?")
    layout.addWidget(label)

    for word_tuple in words:
        word = word_tuple[0]
        label = QLabel(str(word))
        layout.addWidget(label)

    def on_confirm():
        # Call the function that creates the cards and get the number of cards added
        script_dir = os.path.dirname(__file__)
        folder_path = os.path.join(script_dir, 'test-data', 'Digital Editions')
        num_cards_added = create_anki_cards(match_annotations_and_words(words, get_annotations(folder_path)))
        
        # Display a message box with the number of cards added
        QMessageBox.information(dialog, "Cards Added", f"{num_cards_added} cards added")
        
        # Close the original dialog
        dialog.close()

    confirm_button = QPushButton("Confirm")
    confirm_button.clicked.connect(on_confirm)
    layout.addWidget(confirm_button)

    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.close)
    layout.addWidget(cancel_button)

    dialog.exec()

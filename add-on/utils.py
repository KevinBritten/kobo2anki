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
from openai import OpenAI

def get_api_key():
    config = mw.addonManager.getConfig(__name__)
    return config.get("api_key", "")

print(get_api_key())

client = OpenAI(
    # This is the default and can be omitted
    api_key=get_api_key(),
)

def extract_words_from_kobo():
    conn = sqlite3.connect('F:\.kobo\KoboReader.sqlite')
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
    cards_added = 0
    
    # Iterate through the words and create Anki cards
    for pair in pairs:
        word = pair['word']
        matching_annotation = pair['matching_annotation']
        prompt = f"Define {word} in the context of the following sentence. Provide a dictionary type definition. Don't repeat the word, only output the definition: {matching_annotation}"
        response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
        )
        print(response.choices[0])
        definition = response.choices[0].message.content
        # Create a new note
        note = mw.col.new_note(1704410557575)  # Include the reference to the Anki collection
        # Set the word as the front of the card
        note["Back"] = word + ' - ' + definition
        note["Front"] = matching_annotation
      
        mw.col.add_note(note,deck_id)
        cards_added += 1


    mw.reset()
    return cards_added
    


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
        num_cards_added = create_anki_cards(match_annotations_and_words(words, get_annotations("F:/Digital Editions/Annotations/Digital Editions")))
        
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

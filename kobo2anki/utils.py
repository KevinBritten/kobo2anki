# utils.py
import sqlite3
import traceback
from anki.notes import Note
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton

def extract_words_from_kobo():
    conn = sqlite3.connect('E:\.kobo\KoboReader.sqlite')
    cursor = conn.cursor()
    query = "SELECT Text, DateCreated FROM WordList"
    cursor.execute(query)
    words = cursor.fetchall()
    conn.close()
    return words

def get_annotations():
    # Implement the logic to read annotations
    # This could involve reading from a different file or database
    # For now, let's return a simple dictionary for illustration
    all_annotations = {
        'timestamp1': {'text': 'Longtemps, Flora Fontanges a été une voleuse d’âme, ', 'timestamp': '2024-01-01T21:40:25Z'},
        'timestamp2': {'text': 'Annotation 2', 'timestamp': '3:10 PM'},
        'timestamp3': {'text': 'Annotation 3', 'timestamp': '3:15 PM'}
    }
    return all_annotations

def match_annotations_and_words(words, annotations):
    pairs = []
    for word, DateCreated in words:
        matching_annotation = ""
        for annotation in annotations.values():
            if annotation['timestamp'] > DateCreated:
                if word in annotation['text']:
                    matching_annotation = annotation['text']
                break  # Stop searching after finding the first matching annotation
        pairs.append({'word': word, 'matching_annotation': matching_annotation})
    return pairs

def create_anki_cards(pairs):
    deck_name = "Test"
    # Get the default deck ID as an integer
    deck_id = mw.col.decks.id(deck_name)
    print(deck_id)
    
    # Iterate through the words and create Anki cards
    for pair in pairs:
        word = pair['word']
        matching_annotation = pair['matching_annotation']
        print(type(word))
        # Create a new note
        note = mw.col.new_note(1704410557575)  # Include the reference to the Anki collection
        # Set the word as the front of the card
        note["Back"] = word
        note["Front"] = matching_annotation
        print(note.fields)
      
        mw.col.add_note(note,deck_id)


    mw.reset()








def show_confirmation_dialog(words):
    # Create a confirmation dialog
    dialog = QDialog(mw)
    dialog.setWindowTitle("Confirmation")
    dialog.setGeometry(100, 100, 300, 150)

    # Create a layout
    layout = QVBoxLayout(dialog)

    # Add a label
    label = QLabel("Do you want to create Anki cards for the following words?")
    layout.addWidget(label)

    # Add the list of words
    for word_tuple in words:
        word = word_tuple[0]  # Assuming the word is in the first position of the tuple
        label = QLabel(str(word))  # Convert to str to ensure QLabel receives a string
        layout.addWidget(label)


    # Add Confirm and Cancel buttons
    confirm_button = QPushButton("Confirm")
    confirm_button.clicked.connect(lambda: create_anki_cards(match_annotations_and_words(words, get_annotations())))

    layout.addWidget(confirm_button)

    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(dialog.close)
    layout.addWidget(cancel_button)

    # Show the dialog
    dialog.exec()
# utils.py
from anki.notes import Note
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox,QScrollArea,QWidget
import os
import sys
import xml.etree.ElementTree as ET
import concurrent.futures
import requests


lib_path = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.insert(0, lib_path)
config = mw.addonManager.getConfig(__name__)
import deepl


def update_config():
    global config
    config = mw.addonManager.getConfig(__name__)



def definition_func(word, context,source_lang,target_lang):
    server_mode = config.get("server_mode", False)
   
    try:
        if (server_mode):
            server_url = 'http://localhost:3000/translate'
            response = requests.post(server_url, json={
            'text': word,
            'context':context,
            'source_lang':source_lang,
            'target_lang':target_lang
            })
            if response.status_code == 200:
                data = response.json()
                if 'translations' in data and len(data['translations']) > 0:
                    translation = data['translations']['text']
                    return word, context,translation
                else:
                    print("No translations found in the response.")
            else:
                    print("Error:", response.status_code, response.text)
        else:
            api_key = config.get("deepl_api_key", "")
            translator = deepl.Translator(api_key)
            translation = translator.translate_text(word, context=context, source_lang=source_lang, target_lang=target_lang) 
            return word, context,translation.text 
            
    except Exception as e:
        print("Error in translating with DeepL:", str(e))
        return None

def create_anki_cards(annotations):
    # Load the deck ID from the configuration
    deck_id = config.get('selected_deck_id')
    modelID = get_model_id()
    num_cards_added = 0;
    source_lang, target_lang = set_langs()
    results = batch_translate(annotations,source_lang,target_lang)
    for result in results:
        word, annotation_text,definition= result
        note = mw.col.new_note(modelID)  # Include the reference to the Anki collection
        # Set the word as the front of the card
        note["Back"] = word + ' - ' + definition
        note["Front"] = annotation_text
        if mw.col.add_note(note, deck_id):
             num_cards_added+=1
    mw.reset()
    return num_cards_added


def show_confirmation_dialog(annotations,main_menu_dialog):
    dialog = QDialog(mw)
    dialog.setWindowTitle("Confirmation")
    dialog.setGeometry(100, 100, 500, 650)
    layout = QVBoxLayout(dialog)

    label = QLabel("Do you want to create Anki cards for the following words?")
    layout.addWidget(label)
    
    
    # Create a QScrollArea and add it to the main layout.
    scroll_area = QScrollArea(dialog)
    scroll_area.setWidgetResizable(True)
    layout.addWidget(scroll_area)

    # Create a widget to act as a container for your content.
    content_widget = QWidget()
    scroll_area.setWidget(content_widget)

    # Create a layout for your content.
    content_layout = QVBoxLayout(content_widget)

    for annotation in annotations:
        word = annotation['word']
        label = QLabel(str(word))
        content_layout.addWidget(label)

    def on_confirm():
        # Call the function that creates the cards and get the number of cards added
        num_cards_added = create_anki_cards(annotations)
        # Display a message box with the number of cards added
        QMessageBox.information(dialog, "Cards Added", f"{num_cards_added} cards added")
        
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

def extract_words_and_context(selected_books):
    folder_path = get_annotation_folder()
    if not folder_path:
            return

    annotations = []
    # Define namespaces
    namespaces = {'ns': 'http://ns.adobe.com/digitaleditions/annotations', 'dc': 'http://purl.org/dc/elements/1.1/'}

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        #Load config settings
        skip_annotations_with_existing_card = config.get("skip_annotations_with_existing_card", True)
        add_empty_annotations = config.get("add_empty_annotations", False)
        add_single_word_empty_annotations_only = config.get("add_single_word_empty_annotations_only", True)
        deck_id = config.get('selected_deck_id')
        deck_name = mw.col.decks.get(deck_id)['name']
        card_ids = mw.col.find_cards(f'deck:"{deck_name}"')       

        if filename.endswith(".annot"):
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            if (selected_books is not True):
                book_title_element = root.find(".//ns:publication/dc:title", namespaces)
                book_title = None
                if book_title_element is not None:
                    book_title = book_title_element.text
                if ((book_title is None) or  book_title not in selected_books):
                    continue

                
            # Iterate over annotations
            for parent_elem in root.findall(".//ns:annotation", namespaces):
                    # Find the text element under fragment
                    annotation_elem = parent_elem.find(".//ns:target/ns:fragment/ns:text", namespaces)
                    annotation_text = annotation_elem.text if annotation_elem is not None else None                
                    word_elem = parent_elem.find(".//ns:content/ns:text", namespaces)
                    word_elem_content = word_elem.text if word_elem is not None else None 
                    word_text = ""
                    if (skip_annotations_with_existing_card and search_for_annotation_in_cards(annotation_text,card_ids)):
                        continue
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
                        annotations.append({'annotation_text': annotation_text, 'word': word_text})
        elif filename.endswith(".txt"):
            print('.txt')
            # Open and read the file
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()

            # Split the text into sections using double newlines as separators.
            sections = text.split("\n\n")

            # The first section is the book title.
            book_title = sections[0].strip()
            
            if ((selected_books is not True) and ((book_title is None) or  book_title not in selected_books)):
                continue

            # The remaining sections are your datapoints.
            for datapoint in sections[1:]:
                # Each datapoint might have one or two lines.
                lines = datapoint.splitlines()
                annotation_text = lines[0].strip()  # The first line is always the sentence.
                
                if (skip_annotations_with_existing_card and search_for_annotation_in_cards(annotation_text,card_ids)):
                    continue
                
                # Optionally, the second line might be a note.
                if len(lines) > 1 and lines[1].startswith("Note:"):
                    note = lines[1].strip()[len("Note: "):]
                else:
                    note = None
                
                if note is not None or add_empty_annotations:
                    
                    word_text = get_card_back_from_annotation_and_note(note,annotation_text,add_single_word_empty_annotations_only)  
                    
                    if annotation_text is not None and word_text:
                        annotations.append({'annotation_text': annotation_text, 'word': word_text})
    return annotations

def get_card_back_from_annotation_and_note(note,annotation_text,add_single_word_empty_annotations_only):
    if note is None:
            #check for whitespace in annotation_text
        contains_whitespace = any(char.isspace() for char in annotation_text)
        if add_single_word_empty_annotations_only and contains_whitespace:
            return None
        return annotation_text
    elif note.isdigit():
        # Case 1: note is a single number
        words = annotation_text.split()
        index = int(note) - 1
        if 0 <= index < len(words):
            return words[index]
    elif '.' in note and all(part.isdigit() for part in note.split('.')):
        # Case 2: note is of format "num1.num2"
        start_index, end_index = map(int, note.split('.'))
        words = annotation_text.split()
        if 0 <= start_index-1 < len(words) and 0 < end_index <= len(words) and start_index <= end_index:
            return ' '.join(words[start_index-1:end_index])
    else:
        # Case 3: note is a string in any other format
        return note

def get_annotation_folder():
    folder_path = config.get('annotation-directory', '')

    if not folder_path:
        QMessageBox.warning(None, "No Directory Selected", "Please select a directory for annotations.")
        return None

    if not os.path.isdir(folder_path):
        QMessageBox.warning(None, "Invalid Directory", "The selected directory is invalid.")
        return None

    annotation_files = [f for f in os.listdir(folder_path) if (f.endswith(".annot") or f.endswith(".txt"))]
    if not annotation_files:
        QMessageBox.warning(None, "No Annotation Files", "The selected directory does not contain any annotation files.")
        return None

    return folder_path

def search_for_annotation_in_cards(annotation_text,ids):
    result = False
    for id in ids:
         note_front = mw.col.get_card(id).note()["Front"]
         if annotation_text == note_front:
             result = True
             break
    return result

def get_available_languages(type):
    api_key = config.get("deepl_api_key", "")
    translator = deepl.Translator(api_key)
    if type == 'source':
        return [language.code for language in translator.get_source_languages()]
    elif type == 'target':
        return [language.code for language in translator.get_target_languages()]
    
def set_langs():
    source_lang = config.get("source_lang", "")
    target_lang = config.get("target_lang", "EN-GB")
    if (source_lang == 'Auto detect'):
        source_lang = ""
    return source_lang, target_lang

def batch_translate(annotations,source_lang,target_lang):
    results = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(definition_func, annotation['word'], annotation['annotation_text'], source_lang, target_lang)
            for annotation in annotations
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                # Optionally log the error
                print(f"Error processing annotation: {e}")
                continue
    return results

def get_model_id():
    modelID = None  # Initialize modelID to None
    models = mw.col.models.all()  # Retrieve all models in the collection
    for model in models:
        if model['name'] == "Basic":  # Check if the model name is "Basic"
            modelID = model['id']  # Store the model ID in modelID
            break  # Exit the loop once the desired model is found
    return modelID

         
# KOBO2ANKI

## Purpose

KOBO2ANKI is an addon for Anki that allows you to take highlighted passages from your Kobo eReader and create cards based on the translations of those passages using DeepL. This addon requires a DeepL API key.

## Usage

1. **Get a DeepL API Key:**

   - Obtain a DeepL API key and assign it to the `deepl_api_key` property in `Tools > Addons > KOBO2ANKI`.

2. **Highlight a Passage in Kobo:**

   - Highlight a passage in your Kobo eReader. Optionally, add a note for the highlighted passage. If you don't add a note, the entire passage will be translated.
   - In the note, you can specify:
     - **A single word number:** The number of the word in the passage to translate.
     - **A range of words:** Format as `n1.n2`, which will translate all words between and including `n1` and `n2`.
     - **Specific words:** Type the specific word or words within the passage that you want to be translated.

3. **Run the KOBO2ANKI Addon:**

   - Connect your Kobo to your computer and run the KOBO2ANKI addon.

4. **Select the books to import annotaitons from:**

   - Click `Select Books` and chose which books to import annotations from. By default all books will be selected.

5. **Select the Deck:**

   - Open the options menu and choose the deck to which you want the cards to be added.

6. **Set other options:**
   - Set other options as explained below.

## Options

- **`add_empty_annotations`** (boolean, default: `false`)
  - Creates cards based on highlighted passages with no associated note.
- **`add_single_word_empty_annotations_only`** (boolean, default: `true`)
  - If `add_empty_annotations` is set to `true`, highlighted passages with no associated note will only be added if they contain a single word.
- **`annotation-directory`** (string, default:`""`)
  - Directory containing .annot files.
- **`api_mode`** (string, `"deepl"` or `"openai"`, default: `"openai"`)
  - Choose which API to use for translations.
- **`deepl_api_key`** (string)
  - API key for DeepL.
- **`openai_api_key`** (string)
  - API key for OpenAI.
- **`source_lang`** (string, default:`"FR"`)
  - Language to translate from. [Complete list of supported source languages.](https://developers.deepl.com/docs/resources/supported-languages#source-languages).
- **`skip_annotations_with_existing_card`** (boolean, default: `true`)
  - If set to true annotations which match the front of a card in the selected deck will be skipped.
- **`target_lang`** (string, default:`"EN-GB"`)
  - Language to translate to. [Complete list of supported target languages.](https://developers.deepl.com/docs/resources/supported-languages#target-languages).

## Planned Features

- Server mode to allow a small amount of translations without an API key.
- Support for multiple books.
- Selection and handling of individual highlighted passages instead of only bulk add.

## Development

To set up the project:

1. Clone the repository.
2. Note that required packages have been included in the addon as Anki does not support installing dependencies. If you want to reinstall the dependencies, run `update.bat`.

## Contribution

Contributions are welcome! Feel free to open pull requests. Standard contribution guidelines apply.

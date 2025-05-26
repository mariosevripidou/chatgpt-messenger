# ChatGTP Messenger

ChatGTP Messenger is a graphical desktop application that uses OpenAI's GPT models via API. Supports chating, attaching files, extracting text from images (OCR), previewing spreadsheets, and talking using voice input/output.

## Features

- Attach Files (.txt, .pdf, .docx, .csv, .xlsx, .jpg, .png)
- OCR (Extract Text from Images)
- Spreadsheet Previews
- Voice Input/Output
- Save History

## Requirements

- Python 3.8+
- OpenAI API key

## Dependencies

Python Packages: Install dependencies using pip:
```
pip install openai customtkinter speechrecognition pyttsx3 pytesseract pillow pymupdf python-docx simplejson pandas openpyxl python-dotenv
```

Tesseract OCR engine: To enable Optical Character Recognition (OCR) functionality, the Tesseract engine must be installed separately.
- Download for Windows: https://github.com/tesseract-ocr/tesseract#windows
- After installation, ensure the Tesseract executable is added to your system’s PATH.

## Setup
```
git clone https://github.com/mariosevripidou/chatgpt-messenger
cd chatgpt-messenger
```

## How to Run

1. Clone or download the project files.
2. Create a .env file and add your OpenAI API Key.
3. Run the app: python chatgpt_messenger.py

## How to Build Stand-alone EXE

1. Install PyInstaller: pip install pyinstaller
2. Build the app: pyinstaller --noconsole --onefile --name "ChatGPTMessenger" --icon=chatgpt_messenger.ico chatgpt_messenger.py
3. Your .exe will be located inside the /dist/ folder.
4. Copy your .env file next to the .exe after building.

## Files

- chatgpt_messenger.py – Main application logic and interface
- README.md – Project overview and instructions
- requirements.txt – Python package dependency list
- .env – API key and configuration (create it with your API key)
- chatgpt_messenger.ico – Application icon for executable
- memory.json – Chat memory file. Auto-generated after first run)
- dist/ChatGTP_Messenger.exe – Standalone compiled Windows executable. (if you build it)

## Notes
- .env file should follow the format: OPENAI_API_KEY=openai-api-key-goes-here
- .env file must be placed next to the .exe after building.
- Settings (username, colors, voice preference) are automatically saved in memory.json.
- Default model is gpt-3.5-turbo, but you can switch to gpt-4 from Settings.

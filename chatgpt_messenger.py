import openai
import customtkinter as ctk
import threading
import speech_recognition as sr
import pyttsx3
import os
import simplejson as json
import time
import pytesseract
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
from dotenv import load_dotenv
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image

# Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

# Optional: Set tesseract path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Global Variables
model_name = "gpt-3.5-turbo"
memory_file = "memory.json"
engine = pyttsx3.init()

DEFAULT_USER_COLOR = "#3b82f6"
DEFAULT_ASSISTANT_COLOR = "#4000ff"

# Load memory
def load_memory():
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_memory(memory):
    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)

memory_data = load_memory()

# Personalities
personalities = {
    "Friendly Assistant": "You are a friendly and helpful assistant.",
    "Funny Friend": "You are a funny, sarcastic friend who loves jokes.",
    "Calm Therapist": "You are a calm, supportive therapist.",
    "Creative Brainstormer": "You are a creative brainstorming partner full of ideas."
}

# Ask name window if needed
def ask_name_window():
    name_window = ctk.CTk()
    name_window.geometry("400x250")
    name_window.title("Welcome to ChatGTP Messenger!")

    ctk.CTkLabel(name_window, text="Please enter your name:", font=("Arial", 18)).pack(pady=20)
    name_entry = ctk.CTkEntry(name_window, placeholder_text="Your name here...")
    name_entry.pack(pady=10)

    def save_name():
        user_name = name_entry.get().strip()
        if user_name:
            memory_data["name"] = user_name
            save_memory(memory_data)
            name_window.destroy()
            launch_main_app()

    def exit_app():
        name_window.destroy()
        os._exit(0)

    ctk.CTkButton(name_window, text="Let's Start!", command=save_name).pack(pady=10)
    ctk.CTkButton(name_window, text="Exit", command=exit_app).pack(pady=5)

    name_window.mainloop()

# Launch main app
def launch_main_app():
    global user_color, assistant_color, voice_enabled
    global system_message, conversation
    global root, chat_frame, input_field
    global send_button, mic_button, attach_button
    global voice_toggle_button, settings_button, about_button
    global thinking_label, spinner_running

    user_color = memory_data.get("user_color", DEFAULT_USER_COLOR)
    assistant_color = memory_data.get("assistant_color", DEFAULT_ASSISTANT_COLOR)
    voice_enabled = memory_data.get("voice_enabled", True)

    current_personality = personalities["Friendly Assistant"]
    system_message = f"You are a personal assistant helping {memory_data['name']}. {current_personality}"
    conversation = [{"role": "system", "content": system_message}]

    root = ctk.CTk()
    root.title("ChatGTP Messenger")
    root.geometry("600x700")

    chat_frame = ctk.CTkFrame(root)
    chat_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # === INPUT ROW 1: Text + Send + Mic ===
    input_frame_top = ctk.CTkFrame(root)
    input_frame_top.pack(padx=10, pady=(5, 0), fill="x")

    input_field = ctk.CTkEntry(input_frame_top, placeholder_text="Type your message here...", width=300)
    input_field.pack(side="left", padx=5, pady=5, expand=True, fill="x")
    input_field.bind("<Return>", send_message)

    send_button = ctk.CTkButton(input_frame_top, text="Send", command=send_message, width=70)
    send_button.pack(side="left", padx=5)

    mic_button = ctk.CTkButton(input_frame_top, text="🎤", command=send_voice, width=50)
    mic_button.pack(side="left", padx=5)

    # === INPUT ROW 2: Attach + Voice Toggle + Settings + About ===
    input_frame_bottom = ctk.CTkFrame(root)
    input_frame_bottom.pack(padx=10, pady=(5, 10), fill="x")

    attach_button = ctk.CTkButton(input_frame_bottom, text="📎 Attach", command=attach_file, width=100)
    attach_button.pack(side="left", padx=5, pady=5)

    voice_toggle_button = ctk.CTkButton(input_frame_bottom, text="🔊 Voice ON", command=toggle_voice, width=100)
    voice_toggle_button.pack(side="left", padx=5, pady=5)

    settings_button = ctk.CTkButton(input_frame_bottom, text="⚙️ Settings", command=open_settings, width=100)
    settings_button.pack(side="left", padx=5, pady=5)

    about_button = ctk.CTkButton(input_frame_bottom, text="ℹ️ About", command=open_about, width=100)
    about_button.pack(side="left", padx=5, pady=5)

    thinking_label = ctk.CTkLabel(root, text="Thinking...", font=("Arial", 14))
    spinner_running = ctk.BooleanVar(value=False)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

# Attach File
def attach_file():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()

    # Show attached file message
    if ext in [".jpg", ".jpeg", ".png", ".bmp"]:
        answer = messagebox.askyesno("OCR", "Do you want to extract text from this image?")
        if answer:
            try:
                text = pytesseract.image_to_string(Image.open(file_path))
                send_content_message(f"OCR Extracted Text from {filename}:\n\n{text}")
            except Exception as e:
                append_message("System", f"Failed to OCR image: {e}", align="center")
        else:
            append_message("System", f"📷 Attached Image: {filename}", align="center")
    elif ext in [".pdf"]:
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            send_content_message(f"PDF Content from {filename}:\n\n{text}")
        except Exception as e:
            append_message("System", f"Failed to read PDF: {e}", align="center")
    elif ext in [".docx"]:
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            send_content_message(f"Word Content from {filename}:\n\n{text}")
        except Exception as e:
            append_message("System", f"Failed to read DOCX: {e}", align="center")
    elif ext in [".csv", ".xls", ".xlsx"]:
        answer = messagebox.askyesno("Preview Spreadsheet", "Do you want to preview this spreadsheet?")
        if answer:
            try:
                if ext == ".csv":
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                text = df.head(10).to_string()
                send_content_message(f"Spreadsheet Preview from {filename}:\n\n{text}")
            except Exception as e:
                append_message("System", f"Failed to read Spreadsheet: {e}", align="center")
        else:
            append_message("System", f"📄 Attached Spreadsheet: {filename}", align="center")
    elif ext in [".txt", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            send_content_message(f"File Content from {filename}:\n\n{text}")
        except Exception as e:
            append_message("System", f"Failed to read Text File: {e}", align="center")
    else:
        append_message("System", f"📎 Attached File: {filename}", align="center")

def send_content_message(content):
    append_message("You (Attachment)", content, align="right", color=user_color)
    conversation.append({"role": "user", "content": content})
    threading.Thread(target=get_gpt_response).start() 
    
# Helper Functions
def speak(text):
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        append_message("System", "Listening...", align="center", color="#888888")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        append_message("System", "Sorry, I didn't understand.", align="center", color="#888888")
        return ""

def send_message(event=None):
    user_input = input_field.get()
    if not user_input.strip():
        return
    input_field.delete(0, ctk.END)
    append_message("You", user_input, align="right", color=user_color)

    conversation.append({"role": "user", "content": user_input})
    threading.Thread(target=get_gpt_response).start()

def send_voice():
    user_input = listen()
    if user_input:
        append_message("You (Voice)", user_input, align="right", color=user_color)
        conversation.append({"role": "user", "content": user_input})
        threading.Thread(target=get_gpt_response).start()

def get_gpt_response():
    global voice_enabled
    try:
        thinking_label.pack()
        spinner_running.set(True)
        threading.Thread(target=animate_spinner).start()

        response = client.chat.completions.create(
            model=model_name,
            messages=conversation,
            stream=True
        )

        full_reply = ""
        assistant_message = ctk.CTkLabel(chat_frame, text="", wraplength=450, justify="left",
                                         fg_color=assistant_color, corner_radius=10, anchor="w")
        assistant_message.pack(padx=10, pady=5, anchor="w")

        for chunk in response:
            if chunk.choices[0].delta.content:
                part = chunk.choices[0].delta.content
                full_reply += part
                assistant_message.configure(text=assistant_message.cget("text") + part)
                root.update()

        conversation.append({"role": "assistant", "content": full_reply})

        if voice_enabled:
            speak(full_reply)

    except Exception as e:
        append_message("System", f"Error: {e}", align="center", color="#888888")
    finally:
        spinner_running.set(False)
        thinking_label.pack_forget()

def animate_spinner():
    spinner_cycle = ["|", "/", "-", "\\"]
    idx = 0
    while spinner_running.get():
        thinking_label.configure(text=f"ChatGPT is thinking... {spinner_cycle[idx % 4]}")
        idx += 1
        time.sleep(0.2)

def append_message(sender, text, align="left", color="#14b8a6"):
    message = ctk.CTkLabel(chat_frame, text=f"{sender}: {text}", wraplength=450, justify="left",
                           fg_color=color, corner_radius=10, anchor="w")
    if align == "right":
        message.pack(padx=10, pady=5, anchor="e", fill="none")
    elif align == "center":
        message.pack(padx=10, pady=5, anchor="center", fill="none")
    else:
        message.pack(padx=10, pady=5, anchor="w", fill="none")

# Settings
def toggle_voice():
    global voice_enabled
    voice_enabled = not voice_enabled
    memory_data["voice_enabled"] = voice_enabled
    save_memory(memory_data)
    if voice_enabled:
        voice_toggle_button.configure(text="🔊 Voice ON")
    else:
        voice_toggle_button.configure(text="🔇 Voice OFF")

def toggle_voice_in_settings():
    global voice_enabled
    voice_enabled = not voice_enabled
    memory_data["voice_enabled"] = voice_enabled
    save_memory(memory_data)

def open_settings():
    settings_window = ctk.CTkToplevel(root)
    settings_window.geometry("400x500")
    settings_window.title("Settings")

    model_choice = ctk.CTkOptionMenu(settings_window, values=["gpt-3.5-turbo", "gpt-4"],
                                     command=change_model)
    model_choice.set(model_name)
    model_choice.pack(pady=10)

    personality_choice = ctk.CTkOptionMenu(settings_window, values=list(personalities.keys()),
                                           command=change_personality)
    personality_choice.pack(pady=10)

    ctk.CTkButton(settings_window, text="Pick User Color", command=pick_user_color).pack(pady=10)
    ctk.CTkButton(settings_window, text="Pick Assistant Color", command=pick_assistant_color).pack(pady=10)

    voice_checkbox = ctk.CTkCheckBox(settings_window, text="Enable Voice Output", command=toggle_voice_in_settings)
    voice_checkbox.pack(pady=10)
    if voice_enabled:
        voice_checkbox.select()

    reset_button = ctk.CTkButton(settings_window, text="Reset Colors", command=reset_colors)
    reset_button.pack(pady=15)

def change_model(choice):
    global model_name
    model_name = choice

def change_personality(choice):
    global current_personality
    current_personality = personalities[choice]
    conversation.clear()
    conversation.append({"role": "system", "content": f"You are a personal assistant helping {memory_data['name']}. {current_personality}"})
    append_message("System", f"Personality changed to {choice}", align="center", color="#888888")

def pick_user_color():
    global user_color
    color = colorchooser.askcolor(title="Pick User Color")[1]
    if color:
        user_color = color
        memory_data["user_color"] = user_color
        save_memory(memory_data)

def pick_assistant_color():
    global assistant_color
    color = colorchooser.askcolor(title="Pick Assistant Color")[1]
    if color:
        assistant_color = color
        memory_data["assistant_color"] = assistant_color
        save_memory(memory_data)

def reset_colors():
    global user_color, assistant_color
    user_color = DEFAULT_USER_COLOR
    assistant_color = DEFAULT_ASSISTANT_COLOR
    memory_data["user_color"] = user_color
    memory_data["assistant_color"] = assistant_color
    save_memory(memory_data)

# About Page
def open_about():
    about_window = ctk.CTkToplevel(root)
    about_window.geometry("400x300")
    about_window.title("About ChatGTP Messenger")

    ctk.CTkLabel(about_window, text="ChatGPT Messenger", font=("Arial", 20)).pack(pady=10)
    ctk.CTkLabel(about_window, text="Talk. Think. Connect.", font=("Arial", 14)).pack(pady=5)
    ctk.CTkLabel(about_window, text="Version 1.0", font=("Arial", 12)).pack(pady=5)
    ctk.CTkLabel(about_window, text="Licensed under the MIT License © 2025 Marios Evripidou", font=("Arial", 10)).pack(pady=20)

    ctk.CTkButton(about_window, text="Close", command=about_window.destroy).pack(pady=10)

# Closing
def on_closing():
    save_memory(memory_data)
    save_conversation()
    root.destroy()

def save_conversation():
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"chat_history_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for msg in conversation:
            f.write(f"{msg['role'].upper()}: {msg['content']}\n\n")

# --- START APP ---
if "name" not in memory_data:
    ask_name_window()
else:
    launch_main_app()
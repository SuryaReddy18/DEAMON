import speech_recognition as sr
from datetime import datetime
import os

recognizer = sr.Recognizer()


def format_text(text):
    question_keywords = ["what", "why", "how", "where", "when", "who", "is", "are", "do", "does", "can", "could", "should", "would", "will"]
    
    # Convert text to lowercase for accurate checking
    words = text.lower().split()
    
    # If it starts with a question word or doesn’t have punctuation at the end, add a question mark
    if words and (words[0] in question_keywords or not text.endswith(".")):
        return text.strip() + "?"
    return text.strip() + "."

# Function to record and recognize speech
def record_and_recognize():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2.5)  # Adjust for noise
        audio = recognizer.listen(source)  # No timeout, keeps listening
        print("Listening continuously...")  

        while True:  # Keep listening indefinitely
            try:
                audio = recognizer.listen(source)  # No timeout, continuous listening
                text = recognizer.recognize_google(audio)  
                formatted_text = format_text(text)  
                print("You said: " + formatted_text)
                return formatted_text  # ✅ Ensure it returns recognized text
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand what you said.")
            except sr.RequestError:
                print("Could not connect to the speech recognition service.")
            except Exception as e:
                print(f"An error occurred: {str(e)}")


def save_to_html(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_entry = f"""
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Recognized Speech:</strong> {text}</p>
    <hr>
    """

    file_path = "Data/voice.html"
    os.makedirs("Data", exist_ok=True)  

    # Append to file if it exists, else create a new file
    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as file:
            file.write(html_entry)
    else:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f"<html><head><title>Voice Transcript</title></head><body><h1>Speech-to-Text Logs</h1>{html_entry}</body></html>")

# Main function
if __name__ == "__main__":
    recognized_text = record_and_recognize()
    save_to_html(recognized_text)

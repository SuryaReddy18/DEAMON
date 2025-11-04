import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

# Load environment variables safely
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-AU-WilliamNeural")  # Default voice if not set

# Ensure Data directory exists
os.makedirs("Data", exist_ok=True)

async def TextToAudioFile(text, file_path="Data/speech.mp3"):
    """Converts text to speech and saves it as an audio file."""
    if os.path.exists(file_path):
        os.remove(file_path)  # Remove old file
    
    try:
        communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+10Hz', rate='+5%')
        await communicate.save(file_path)
    except Exception as e:
        print(f"Error in TextToAudioFile: {e}")

def play_audio(file_path="Data/speech.mp3", func=lambda r=None: True):
    """Plays the generated speech audio file using Pygame."""
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if not func():
                break

    except Exception as e:
        print(f"Error in play_audio: {e}")
    
    finally:
        try:
            func(False)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error in finally block: {e}")

def TTS(text, func=lambda r=None: True):
    """Handles text-to-speech conversion & playback."""
    asyncio.run(TextToAudioFile(text))
    play_audio(func=func)

def TextToSpeech(text, func=lambda r=None: True):
    """Splits long text into smaller chunks and plays them sequentially."""
    max_chunk_size = 200  # Limit per chunk for better speech clarity
    sentences = text.split(". ")  # Split by sentence

    # If text is too long, break it into smaller parts
    if len(text) > max_chunk_size:
        print("Long text detected, splitting into multiple parts...")
        for i in range(0, len(sentences), 2):  # Speak two sentences at a time
            chunk = ". ".join(sentences[i:i+2])  # Join two sentences
            TTS(chunk, func)
    else:
        TTS(text, func)

if __name__ == "__main__":
    while True:
        try:
            user_input = input("Enter text: ").strip()
            if not user_input:
                print("Please enter some text.")
                continue
            TextToSpeech(user_input)
        except KeyboardInterrupt:
            print("\nExiting...")
            break

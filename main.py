from Frontend.GUI import (
    GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen, TempDirectoryPath,
    SetMicrophoneStatus, AnswerModifier, QueryModifier, GetMicrophoneStatus, GetAssistantStatus
)
from Backend.Model import FirstLawyerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import record_and_recognize
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech
from dotenv import dotenv_values
from asyncio import run
import asyncio
import subprocess
import threading
import os
import json
import re
from Backend.Automation import Automation, CheckBattery, CheckCPU
import speech_recognition as sr
import time


# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
DefaultMessage = f"""{Username}:Hello {Assistantname}, How are you sir!
{Assistantname}:Welcome {Username}. I am at your service any time sir!"""
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search", "generate image", "reminder"]

def ShowDefaultChatIfNoChats():
    """Show default chat if no chats are available."""
    File = open(r'Data\ChatLog.json', "r", encoding='utf-8')
    if len(File.read()) < 5:
        with open(TempDirectoryPath('Database.data'), "w", encoding='utf-8') as file:
            file.write("")
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
            file.write(DefaultMessage)
def process_speech_command(command):
    print(f"🎤 Recognized Command: {command}")  # ✅ Debugging Log
    
    # ✅ Ensure correct formatting
    command = command.lower().strip()
    
    # ✅ Send command to Automation()
    asyncio.run(Automation([command]))  

def ReadChatLogJson():
    """Read chat log from JSON file."""
    with open(r'Data\ChatLog.json', "r", encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():
    """Integrate chat log into the database."""
    json_data = ReadChatLogJson()
    formatted_chatlog = ""

    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"user:{entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"Assistant:{entry['content']}\n"

    formatted_chatlog = formatted_chatlog.replace("User", Username + " ")
    formatted_chatlog = formatted_chatlog.replace("Assistant", Assistantname + " ")

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    """Display chats on the GUI."""
    File = open(TempDirectoryPath('Database.data'), "r", encoding='utf-8')
    Data = File.read()
    if len(Data) > 0:
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
            file.write(Data)

def generate_image(prompt):
    if not prompt or prompt.lower() in ["anything", "something", "a picture"]:
        prompt = "random artistic scenery"
    image_data_path = os.path.join("Frontend", "Files", "ImageGeneration.data")
    with open(image_data_path, "w") as file:
        file.write(f"{prompt},True")
    try:
        subprocess.Popen(['python', os.path.join('Backend', 'ImageGeneration.py')],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         stdin=subprocess.PIPE, shell=False)
    except Exception as e:
        print(f"Error starting ImageGeneration.py: {e}")

def InitialExecution():
    """Initialize the application."""
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

# Initialize the application
InitialExecution()

def MainExecution():
    """Main execution logic for processing user queries."""
    SetAssistantStatus("Listening...")
    Query = record_and_recognize().strip()
    Query = re.sub(r"[^\w\s]", "", Query)  # ✅ Remove special characters

    Decision = FirstLawyerDMM(Query)  # ✅ Assign Decision BEFORE using it
    print(f"\n✅ Cleaned Decision: {Decision}\n")  # ✅ Debugging log

    for q in Decision:
        if "generate image" in q or "generate an image of" in q:
            # Extract and clean the prompt
            image_prompt = re.sub(r"generate (an )?image( of)?", "", q).strip()
            if not image_prompt:
                image_prompt = "random artistic scenery"  # Default prompt if user says 'anything'

            # Provide immediate response to the user
            ShowTextToScreen(f"{Assistantname}: Generating an image of {image_prompt}...")
            print(f"\n🎨 Generating an image of: {image_prompt}\n")  # Debugging output
            TextToSpeech(f"Generating an image of {image_prompt}")  
            generate_image(image_prompt)
            return

    ShowTextToScreen(f"{Username}: {Query}")
    SetAssistantStatus("Analyzing...")

    # ✅ Handle battery percent queries
    for query in Decision:
        if "battery percent" in query or "battery status" in query:
            Answer = CheckBattery()
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            TextToSpeech(Answer)
            return
    
    # ✅ Handle CPU usage queries
    for query in Decision:
        if "cpu usage" in query or "cpu status" in query:
            Answer = CheckCPU()
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            TextToSpeech(Answer)
            return

    # ✅ Handle other commands normally
    run(Automation(list(Decision)))



    # ✅ Handle "Create File/Folder" Commands
    for query in Decision:
        if query.startswith("create file") or query.startswith("create folder"):
            print(f"🛠️ Sending to Automation: {query}")  # ✅ Debugging log
            run(Automation([query]))  # ✅ Send to Automation
            ShowTextToScreen(f"{Assistantname}: Successfully processed {query}.")
            return                                          
    # ✅ Handle "Play" Commands (Music/Video)                      
    for query in Decision:
        if query.startswith("play"):
            SetAssistantStatus("Playing Song...")
            
            # Check if the query specifies Spotify
            if "on spotify" in query.lower():
                # Format the query for Spotify
                song_name = query.replace("play ", "").replace("on spotify", "").strip()
                run(Automation([f"play {song_name} on spotify"]))  # Send to Automation.py
            else:
                # Default to YouTube
                run(Automation([query]))  # Send to Automation.py
            
            ShowTextToScreen(f"{Assistantname}: Playing {query.replace('play ', '')}.")
            return  
        

    
    # ✅ Handle Reminder Queries (Send to ChatBot)
    for query in Decision:
        if query.startswith("reminder"):
            SetAssistantStatus("Setting Reminder...")
            ReminderText = query.replace("reminder ", "").strip()
            Answer = ChatBot(QueryModifier(f"Set a reminder for {ReminderText}"))  # ✅ Send to ChatBot
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Reminder Set.")
            TextToSpeech(Answer)
            return  # Exit after processing reminder request

    # ✅ Handle Content Queries (Send to ChatBot Instead of Automation)
    for query in Decision:
        if query.startswith("content"):
            QueryFinal = query.replace("content ", "").strip()
            
            # **Check if it's a programming/coding request**
            if any(word in QueryFinal.lower() for word in ["code", "program", "script"]):
                SetAssistantStatus("Generating Code...")
                Answer = ChatBot(QueryModifier(QueryFinal))  # ✅ Send to ChatBot
            else:
                SetAssistantStatus("Searching...")
                Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))  # ✅ Send to RealtimeSearchEngine

            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return  # Exit after processing content creation

    # ✅ Handle Realtime Queries  
    for query in Decision:
        if query.startswith("realtime"):
            QueryFinal = query.replace("realtime ", "").strip()
            print(f"🌐 Fetching real-time info for: {QueryFinal}")  # Debugging log
            SetAssistantStatus("Fetching real-time data...")
            Answer = RealtimeSearchEngine(QueryModifier(QueryFinal))  # ✅ Fetch real-time info
            ShowTextToScreen(f"{Assistantname}: {Answer}")
            SetAssistantStatus("Answering...")
            TextToSpeech(Answer)
            return  # ✅ Exit after processing real-time query


    # ✅ Handle General Queries (ChatBot)  
    if any("general" in q for q in Decision):
        QueryFinal = " ".join(q.replace("general", "").strip() for q in Decision if q.startswith("general"))
        SetAssistantStatus("Thinking...")
        Answer = ChatBot(QueryModifier(QueryFinal))
        ShowTextToScreen(f"{Assistantname}: {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return
    
    if query.startswith("copy"):
        print(f"🛠️ Sending to Automation: {query}")  # ✅ Debugging log
        run(Automation([query]))  # ✅ Send to Automation
        ShowTextToScreen(f"{Assistantname}: Successfully copied {query}.")
        TextToSpeech(f"Successfully copied sir.")  # ✅ Add Voice Feedback
        return  # ✅ Ensure execution

    # ✅ Handle Automation Tasks  
    if any(q.startswith(tuple(Functions)) for q in Decision):
        run(Automation(list(Decision)))
        return

    # ✅ Exit Condition  
    if "exit" in Decision:
        TextToSpeech("Bye Sir!")
        os._exit(10)


recognizer = sr.Recognizer()
listening = True  # ✅ Control listening state globally

def record_and_recognize():
    global listening  # Access the global flag
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2.5)
        print("🎤 Listening...")  

        while True:  # Keep listening indefinitely
            if not listening:
                print("⏸️ Listening Paused. Say 'Wake up' to resume.")
                
                # Keep listening for the "wake up" command
                while not listening:
                    try:
                        audio = recognizer.listen(source)  
                        text = recognizer.recognize_google(audio).lower()
                        print(f"Paused Mode Heard: {text}")

                        if "wake up" in text:
                            listening = True  # ✅ Resume listening
                            print("▶️ Resuming listening...")

                    except sr.UnknownValueError:
                        continue  # Keep waiting for "wake up"
                    except sr.RequestError:
                        print("❌ Could not connect to the speech recognition service.")
                    except Exception as e:
                        print(f"❌ Error: {str(e)}")
            
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio).lower()
                print("You said: " + text)

                if "hold on a sec" in text:
                    listening = False  # ✅ Pause listening
                    print("⏸️ Listening paused.")

                return text  # ✅ Ensure recognized text is returned

            except sr.UnknownValueError:
                print("❌ Sorry, I couldn't understand what you said.")
            except sr.RequestError:
                print("❌ Could not connect to the speech recognition service.")
            except Exception as e:
                print(f"❌ An error occurred: {str(e)}")



def FirstLawyerDMM(query):
    """
    Decision-Making Model to categorize user queries.
    """
    query = query.lower().strip()
    decisions = []

    # ✅ Detect Real-Time Queries (Sports, Stocks, Weather, News)
    if any(word in query for word in ["latest update", "news", "weather", "current", "stock price", "crypto", "gold price","what is latest","what is current","what is"]):
        decisions.append(f"realtime {query}")  # ✅ Mark as real-time query

    # ✅ Handle "Create File" or "Create Folder" Commands
    elif query.startswith("create file") or query.startswith("create folder"):
        decisions.append(query)  # Add the query as-is for automation
        
    elif query.startswith("copy"):
        decisions.append(query)
        ShowTextToScreen(f"{Assistantname}: Successfully copied{query}.")

    # ✅ Handle "Play" Commands
    elif query.startswith("play"):
        decisions.append(query)  # Add the query as-is for automation

    # ✅ Handle Other Commands (e.g., "open", "close", "reminder", etc.)
    elif any(query.startswith(func) for func in ["open", "close", "reminder", "system"]):
        decisions.append(query)

    # ✅ If not categorized above, classify as "general"
    else:
        decisions.append(f"general {query}")

    return decisions

def FirstThread():
    """First thread for handling user queries."""
    while True:
        if GetMicrophoneStatus() == "True":
            MainExecution()
        SetAssistantStatus("Available...")

def SecondThread():
    """Second thread for running the GUI."""
    GraphicalUserInterface()

if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
    
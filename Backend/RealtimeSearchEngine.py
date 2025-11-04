from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import requests
from bs4 import BeautifulSoup


# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = "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"

client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI personal assistant named {Assistantname} which has real-time up-to-date information sir! .
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***
*** Reply in only English, even if the question is in Hindi, reply in English.***"""

try:
    with open(r"ChatLog.json", "r") as f:
        messages = load(f)
except:
    with open(r"ChatLog.json", "w") as f:
        dump([], f)

def ScrapeWebContent(url):
    """Scrapes and summarizes content from a news article."""
    try:
        headers = {"User-Agent": "google.com"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Try extracting article text from common news website structures
        article_paragraphs = soup.find_all("p")
        article_text = " ".join([para.get_text() for para in article_paragraphs])

        if len(article_text) < 500:  # If article is too short, discard it
            return None

        # Summarize the article (first 2-3 sentences)
        sentences = article_text.split(". ")
        summary = ". ".join(sentences[:3]) + "."
        return f"📰 {summary}"

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def GoogleSearch(query):
    """Search Google and return summarized content from the top result."""
    try:
        search_results = list(search(query, num_results=5))  # Fetch top 5 URLs
        
        for url in search_results:
            content = ScrapeWebContent(url)
            if content:
                return content  # Return summarized content if found
        
        return f"No detailed information available. You can check these sources:\n" + "\n".join(search_results)

    except Exception as e:
        return f"Error occurred during Google search: {e}"



def AnswerModifier(Answer):
    """Remove empty lines from the answer."""
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = '\n'.join(non_empty_lines)
    return modified_answer

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "hello , how can i help you ?"},
]

def Information():
    """Provide real-time information like date, time, etc."""
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")
    data = f"please use this real-time information,\n"
    data += f"Day:{day}\n"
    data += f"Date:{date}\n"
    data += f"Month:{month}\n"
    data += f"Year:{year}\n"
    data += f"Time:{hour} hours,{minute} minutes,{second} seconds.\n"
    return data

def RealtimeSearchEngine(prompt):
    """Fetch real-time information and generate a clean response."""
    global SystemChatBot, messages

    with open(r"ChatLog.json", "r") as f:
        messages = load(f)

    messages.append({"role": "user", "content": f"{prompt}"})

    # Perform Google Search and fetch summarized content
    search_results = GoogleSearch(prompt)
    if isinstance(search_results, str):
        return search_results  # If an error occurs, return it

    # Generate response using Groq AI
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=SystemChatBot + [{"role": "system", "content": Information()}] + messages,
        temperature=0.7,
        max_tokens=2048,
        top_p=1,
        stream=True,
        stop=None
    )

    Answer = " "
    for chunk in completion:
        if chunk.choices[0].delta.content:
            Answer += chunk.choices[0].delta.content

    Answer = Answer.strip().replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    with open(r"ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    SystemChatBot.pop()
    return AnswerModifier(Answer=Answer)


if __name__ == "__main__":
    while True:
        prompt = input("Enter Your Query: ")
        print(RealtimeSearchEngine(prompt))
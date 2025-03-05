from flask import Flask, render_template
import openai, os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
import threading

app = Flask(__name__)

api_key = os.getenv("OPENAI_API_KEY")

def fetch_ai_news():
    """Fetches latest AI news using OpenAI API."""
    prompt = "Give me the 5 hottest and most impactful AI news topics right now with a short summary."
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are an AI news aggregator."},
                  {"role": "user", "content": prompt}]
    )
    news_text = response.choices[0].message.content
    
    news_list = []
    for line in news_text.split("\n"):
        if line.strip():
            parts = line.split("-", 1)
            if len(parts) == 2:
                news_list.append({"title": parts[0].strip(), "summary": parts[1].strip()})
    
    from pathlib import Path
    speech_file_path = Path(__file__).parent / "speech.mp3"
    response = openai.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input="The quick brown fox jumped over the lazy dog."
        )
    response.stream_to_file(speech_file_path)

    return news_list[:5]

    

def generate_dialogue(news):
    """Generates a dialogue between two AI agents discussing AI news."""
    dialogue = f"""
    Agent Alpha: "Did you catch the latest AI news? {news[0]['title']} is the talk of the town!"
    Agent Beta: "Absolutely! {news[0]['summary']} But I'm more intrigued by {news[1]['title']}."
    Agent Alpha: "Yeah, {news[1]['summary']} could change the industry."
    """
    return dialogue

def send_email(newsletter):
    """Sends the generated newsletter via email."""
    sender_email = "your_email@example.com"
    receiver_email = "subscriber@example.com"
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "🔥 Daily AI Insights"
    msg.attach(MIMEText(newsletter, 'plain'))

    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login(sender_email, "your_password")
        server.sendmail(sender_email, receiver_email, msg.as_string())

@app.route('/')
def index():
    news = fetch_ai_news()
    newsletter = generate_dialogue(news)
    return render_template('index.html', newsletter=newsletter)

def daily_newsletter_job():
    news = fetch_ai_news()
    newsletter = generate_dialogue(news)
    send_email(newsletter)

schedule.every().day.at("07:00").do(daily_newsletter_job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)

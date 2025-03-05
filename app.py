from flask import Flask, render_template
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import schedule
import time
import threading

app = Flask(__name__)

def fetch_ai_news():
    """Scrapes latest AI news and returns top 5 hot topics."""
    # Placeholder for actual web scraping implementation
    return [
        {"title": "Titan-AI Breaks Records", "summary": "Titan-AI achieves groundbreaking results on industry benchmarks."},
        {"title": "EU AI Regulation Looms", "summary": "Europe plans new policies that could reshape AI deployments."},
        {"title": "Big Tech's AI Arms Race", "summary": "Rumors of a major open-source AI collaboration stir industry."},
        {"title": "AI Art Sparks Controversy", "summary": "Debate rages over AI-generated art in galleries."},
        {"title": "Quantum AI Gains Traction", "summary": "Quantum computing advances could transform AI."}
    ]

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

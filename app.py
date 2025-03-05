from flask import Flask, render_template, request, send_file
import openai
import os
from pathlib import Path
import threading
import schedule
import time

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

def fetch_ai_news():
    """Fetches the latest AI news using OpenAI's language model."""
    prompt = "Provide the 5 most recent and impactful AI news topics with brief summaries."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI news aggregator."},
            {"role": "user", "content": prompt}
        ]
    )
    news_text = response.choices[0].message['content'].strip()
    news_list = []
    for line in news_text.split("\n"):
        if line.strip():
            parts = line.split("-", 1)
            if len(parts) == 2:
                news_list.append({"title": parts[0].strip(), "summary": parts[1].strip()})
    return news_list[:5]

def generate_dialogue(news):
    """Generates a dialogue between two AI agents discussing AI news."""
    dialogue = f"""
    Agent Alpha: "Did you hear about {news[0]['title']}? It's making waves in the AI community."
    Agent Beta: "Yes, {news[0]['summary']}. What are your thoughts on {news[1]['title']}?"
    Agent Alpha: "{news[1]['summary']}. It's a significant development."
    """
    return dialogue.strip()

def synthesize_speech(text, voice, filename):
    """Converts text to speech using OpenAI's TTS API and saves it as an MP3 file."""
    speech_file_path = Path(__file__).parent / filename
    response = openai.Audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    response.stream_to_file(speech_file_path)
    return speech_file_path

@app.route('/')
def index():
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)
    return render_template('index.html', dialogue=dialogue)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)
    voice_alpha = request.form.get('voice_alpha', 'voice_1')
    voice_beta = request.form.get('voice_beta', 'voice_2')

    # Split dialogue into individual lines for each agent
    lines = dialogue.split('\n')
    alpha_lines = [line for line in lines if line.startswith("Agent Alpha:")]
    beta_lines = [line for line in lines if line.startswith("Agent Beta:")]

    # Synthesize speech for each agent
    alpha_speech = synthesize_speech(" ".join(alpha_lines), voice_alpha, 'alpha_speech.mp3')
    beta_speech = synthesize_speech(" ".join(beta_lines), voice_beta, 'beta_speech.mp3')

    # Combine the two speech files into one (this step requires an audio processing library like pydub)
    combined_speech_path = Path(__file__).parent / 'combined_speech.mp3'
    from pydub import AudioSegment
    alpha_audio = AudioSegment.from_mp3(alpha_speech)
    beta_audio = AudioSegment.from_mp3(beta_speech)
    combined_audio = alpha_audio + beta_audio
    combined_audio.export(combined_speech_path, format="mp3")

    return send_file(combined_speech_path, as_attachment=True, download_name='dialogue.mp3')

def daily_newsletter_job():
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)
    # Implement your email sending functionality here

schedule.every().day.at("07:00").do(daily_newsletter_job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)

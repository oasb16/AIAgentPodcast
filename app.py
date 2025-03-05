from flask import Flask, render_template, request
import openai
import boto3
import os
import schedule
import time
import threading
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure AWS S3
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

def fetch_ai_news():
    """Fetches latest AI news using OpenAI API."""
    logger.info("Fetching AI news from OpenAI...")
    try:
        prompt = "Provide the 5 hottest and most impactful AI news topics right now with a short summary."
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

        logger.info("Successfully fetched AI news.")
        return news_list[:5]
    except Exception as e:
        logger.error(f"Error fetching AI news: {e}")
        return []

def generate_dialogue(news):
    """Generates a dialogue between two AI agents discussing AI news."""
    if not news:
        return ["Agent Alpha: No news available.", "Agent Beta: Let's try again later."]
    
    dialogue = [
        f"Agent Alpha: Did you catch the latest AI news? {news[0]['title']} is the talk of the town!",
        f"Agent Beta: Absolutely! {news[0]['summary']} But I'm more intrigued by {news[1]['title']}.",
        f"Agent Alpha: Yeah, {news[1]['summary']} could change the industry."
    ]
    logger.info("Generated AI dialogue successfully.")
    return dialogue

def synthesize_speech(text, voice, filename):
    """Synthesizes speech using OpenAI's TTS and uploads to S3."""
    try:
        logger.info(f"Synthesizing speech with voice: {voice}")
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save the audio file locally
        with open(filename, 'wb') as audio_file:
            audio_file.write(response.content)

        # Upload to S3
        s3.upload_file(
            Filename=filename,
            Bucket=BUCKET_NAME,
            Key=filename,
            ExtraArgs={"ContentType": "audio/mpeg"}
        )

        # Generate the S3 URL
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        logger.info(f"Uploaded {filename} to S3: {s3_url}")
        return s3_url
    except Exception as e:
        logger.error(f"Error in speech synthesis: {e}")
        return None

@app.route('/')
def index():
    logger.info("Rendering index page...")
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)
    return render_template('index.html', dialogue=dialogue)

@app.route('/synthesize', methods=['POST'])
def synthesize():
    logger.info("Synthesis requested...")
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)

    alpha_lines = [line for line in dialogue if line.startswith("Agent Alpha")]
    beta_lines = [line for line in dialogue if line.startswith("Agent Beta")]

    alpha_speech_url = synthesize_speech(" ".join(alpha_lines), "nova", 'alpha_speech.mp3')
    beta_speech_url = synthesize_speech(" ".join(beta_lines), "alloy", 'beta_speech.mp3')

    if not alpha_speech_url or not beta_speech_url:
        logger.error("Speech synthesis failed. Check OpenAI API or S3 upload.")

    return render_template('index.html', dialogue=dialogue, alpha_speech_url=alpha_speech_url, beta_speech_url=beta_speech_url)

def daily_newsletter_job():
    logger.info("Running scheduled daily newsletter job...")
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)
    # Implement email sending logic here

schedule.every().day.at("07:00").do(daily_newsletter_job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)

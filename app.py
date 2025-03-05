from flask import Flask, render_template, request, jsonify
import openai
import boto3
import os
import logging
import schedule
import time
import threading
from gtts import gTTS  # Alternative for text-to-speech

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
    try:
        logger.info("Fetching latest AI news...")

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

        logger.info("AI news fetched successfully.")
        return news_list[:5]

    except Exception as e:
        logger.error(f"Error fetching AI news: {e}")
        return []

def generate_dialogue(news):
    """Generates a conversation between AI agents discussing AI news."""
    try:
        if not news:
            logger.warning("No AI news available to generate dialogue.")
            return ["Agent Alpha: Seems like there's no AI news today.", 
                    "Agent Beta: Yeah, let's check again later."]

        logger.info("Generating AI dialogue based on news...")

        dialogue = [
            f"Agent Alpha: Did you catch the latest AI news? {news[0]['title']} is the talk of the town!",
            f"Agent Beta: Absolutely! {news[0]['summary']} But I'm more intrigued by {news[1]['title']}.",
            f"Agent Alpha: Yeah, {news[1]['summary']} could change the industry."
        ]

        logger.info("Dialogue generation complete.")
        return dialogue

    except Exception as e:
        logger.error(f"Error generating dialogue: {e}")
        return []

def synthesize_full_dialogue(dialogue, filename):
    """
    Synthesizes an entire dialogue into a single MP3 file.
    Uses Google gTTS instead of FFmpeg.
    """
    try:
        logger.info("Synthesizing full dialogue...")

        full_text = " ".join(dialogue)
        speech = gTTS(text=full_text, lang="en", slow=False)  # Google TTS

        # Save synthesized speech
        speech.save(filename)
        logger.info(f"Final synthesized dialogue saved as: {filename}")

        return filename

    except Exception as e:
        logger.error(f"Error in synthesizing full dialogue: {e}")
        return None

def upload_to_s3(filename):
    """Uploads a file to AWS S3 and returns its public URL."""
    try:
        s3.upload_file(
            Filename=filename,
            Bucket=BUCKET_NAME,
            Key=filename,
            ExtraArgs={"ContentType": "audio/mpeg"}
        )
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
        logger.info(f"Uploaded synthesized dialogue to S3: {s3_url}")

        # Cleanup local file after upload
        os.remove(filename)

        return s3_url
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return None

@app.route('/')
def index():
    logger.info("Rendering index page...")
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    logger.info("Synthesis requested...")

    # Fetch AI news & dialogue
    news = fetch_ai_news()
    dialogue = generate_dialogue(news)

    # Generate single MP3 file from entire conversation
    final_audio_file = "full_dialogue.mp3"
    synthesized_file = synthesize_full_dialogue(dialogue, final_audio_file)

    # Upload to S3 and get URL
    speech_url = upload_to_s3(synthesized_file) if synthesized_file else None

    if not speech_url:
        logger.error("Synthesized file upload failed.")

    return jsonify({"dialogue": dialogue, "speech_url": speech_url})

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)

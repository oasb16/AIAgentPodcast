from flask import Flask, render_template, request
import openai
import boto3
import os
import schedule
import time
import threading
import logging
from pydub import AudioSegment

# Set FFMPEG path manually
AudioSegment.converter = "/app/vendor/ffmpeg/bin/ffmpeg"
AudioSegment.ffmpeg = "/app/vendor/ffmpeg/bin/ffmpeg"
AudioSegment.ffprobe = "/app/vendor/ffmpeg/bin/ffprobe"

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

def synthesize_full_dialogue(dialogue, filename):
    """
    Synthesizes an entire dialogue (both agents) into a single MP3 file.
    Uses OpenAI TTS for different voices sequentially.
    """
    try:
        logger.info("Synthesizing full dialogue...")

        combined_audio = AudioSegment.silent(duration=0)  # Start with empty audio

        for line in dialogue:
            # Assign voices based on speaker
            if line.startswith("Agent Alpha"):
                voice = "nova"
            elif line.startswith("Agent Beta"):
                voice = "alloy"
            else:
                continue  # Skip lines that don’t match either agent

            logger.info(f"Synthesizing speech: {line} with voice {voice}")

            # Generate speech for this dialogue line
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=line
            )

            temp_filename = f"temp_{voice}.mp3"
            with open(temp_filename, 'wb') as audio_file:
                audio_file.write(response.content)

            # Load and append generated speech to the final file
            segment = AudioSegment.from_file(temp_filename, format="mp3")

            # Add silence between dialogues for natural pauses
            silence = AudioSegment.silent(duration=500)  # 500ms pause
            combined_audio += segment + silence

            # Clean up temp file
            os.remove(temp_filename)

        # Export final combined file
        combined_audio.export(filename, format="mp3")
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

    return render_template('index.html', dialogue=dialogue, speech_url=speech_url)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    threading.Thread(target=run_scheduler, daemon=True).start()
    app.run(debug=True)

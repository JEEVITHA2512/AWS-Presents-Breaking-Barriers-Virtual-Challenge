import asyncio
import pyaudio
import webrtcvad
import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import sys
import subprocess
from tempfile import gettempdir
import cv2
import time
import json

# Configuration
REGION = "us-east-1"  # Nova is supported in this region
SAMPLE_RATE = 16000
FRAME_DURATION = 30
SILENCE_THRESHOLD = 5  # seconds
FACE_DETECTION_INTERVAL = 1  # seconds

# Global
transcriptions = []

# AWS Clients
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)
session = boto3.Session()
polly = session.client("polly")

# Face detection
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Transcribe Event Handler
class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        global transcriptions
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                transcriptions.append(alt.transcript.lower())

def open_audio_stream(pyaudio_instance):
    frame_size = int(SAMPLE_RATE * FRAME_DURATION / 1000)
    return pyaudio_instance.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=frame_size
    )

async def handle_audio_stream(stream, vad, pyaudio_instance):
    silence_start = time.time()
    stream_in = open_audio_stream(pyaudio_instance)

    while True:
        data = stream_in.read(int(SAMPLE_RATE * FRAME_DURATION / 1000), exception_on_overflow=False)
        if vad.is_speech(data, SAMPLE_RATE):
            await stream.input_stream.send_audio_event(audio_chunk=data)
            silence_start = time.time()
        elif time.time() - silence_start > SILENCE_THRESHOLD:
            break
        await asyncio.sleep(0)

    await stream.input_stream.end_stream()
    stream_in.stop_stream()
    stream_in.close()
    pyaudio_instance.terminate()

async def process_transcription():
    transcribe_client = TranscribeStreamingClient(region=REGION)
    stream = await transcribe_client.start_stream_transcription(
        language_code="en-US",
        media_sample_rate_hz=SAMPLE_RATE,
        media_encoding="pcm",
    )

    vad = webrtcvad.Vad()
    vad.set_mode(1)  # Aggressive mode
    pyaudio_instance = pyaudio.PyAudio()
    handler = MyEventHandler(stream.output_stream)

    tasks = [
        handle_audio_stream(stream, vad, pyaudio_instance),
        handler.handle_events(),
    ]

    await asyncio.gather(*tasks)

def send_to_nova():
    global transcriptions
    if not transcriptions:
        print("No transcriptions to send.")
        return

    request_body = {
        "system": [
            {
                "text": "You are Nephele, an Institutional Voice Chatting Intelligent Robot. You interact with participants during events and students during classes."
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [{"text": transcriptions[-1]}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 1000,
            "temperature": 0.5,
            "topP": 0.9
        }
    }

    try:
        response = bedrock_client.invoke_model(
            modelId="amazon.nova-micro-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        response_text = response_body['output']['message']['content'][0]['text']
        print("Response from Amazon Nova:")
        print(response_text)
        return response_text

    except ClientError as e:
        print(f"ERROR: Failed to invoke Amazon Nova. Reason: {e}")
        return None

def start_face_detection():
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("Could not open webcam.")
        sys.exit(-1)

    print("Starting face detection...")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to capture frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) > 0:
            print("Face detected. Starting transcription...")
            video_capture.release()
            cv2.destroyAllWindows()
            return True

        time.sleep(FACE_DETECTION_INTERVAL)

    video_capture.release()
    cv2.destroyAllWindows()
    return False

def split_text(text, max_length=3000):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def play_audio(output_file):
    if sys.platform == "win32":
        os.startfile(output_file)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, output_file])

def synthesize_speech(response_text):
    try:
        text_chunks = split_text(response_text)
        output_file = os.path.join(gettempdir(), "combined_speech.mp3")

        with open(output_file, "wb") as out_file:
            for chunk in text_chunks:
                response = polly.synthesize_speech(Text=chunk, OutputFormat="mp3", VoiceId="Joanna")
                if "AudioStream" in response:
                    with closing(response["AudioStream"]) as stream:
                        out_file.write(stream.read())
                else:
                    print("No audio stream.")
                    sys.exit(-1)

        play_audio(output_file)

    except (BotoCoreError, ClientError) as error:
        print(error)
        sys.exit(-1)

def main():
    start_time = time.time()

    if start_face_detection():
        asyncio.run(process_transcription())
        response_text = send_to_nova()
        if response_text:
            synthesize_speech(response_text)

    latency = time.time() - start_time
    print(f"Total latency: {latency:.2f} seconds")

if __name__ == "__main__":
    main()

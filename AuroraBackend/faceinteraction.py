import asyncio
import pyaudio
import webrtcvad
import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing, asynccontextmanager
import os
import sys
import subprocess
from tempfile import gettempdir
import cv2  # For face detection
import time

''' This code first opens the camera and looks for a human face, once a human face is detected, the transcription stream is started which transcribes the 
voice input from the user into text and sends this text output as input to a bedrock model using the converse api. The text response from the bedrock model is 
converted to speech using Amazon polly and the output is played back to the user using pyaudio'''

# Configuration parameters
REGION = "ap-south-1"
SAMPLE_RATE = 16000
FRAME_DURATION = 30
SILENCE_THRESHOLD = 5  # seconds
LOOP_DURATION = 10  # seconds

# Global variable to store transcriptions
transcriptions = []

# Initialize Boto3 Bedrock client
bedrock_client = boto3.client('bedrock-runtime', region_name=REGION)

# Amazon Polly setup
session = boto3.Session()
polly = session.client("polly")

# Face detection parameters
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # Haar cascade XML file path for face detection
FACE_DETECTION_INTERVAL = 1  # seconds

class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        global transcriptions
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                command = alt.transcript.lower()
                transcriptions.append(command)  # Append each transcript

@asynccontextmanager
async def open_audio_stream(pyaudio_instance):
    frame_size = int(SAMPLE_RATE * FRAME_DURATION / 1000)
    stream_in = pyaudio_instance.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=SAMPLE_RATE,
                                      input=True,
                                      frames_per_buffer=frame_size)
    try:
        yield stream_in
    finally:
        stream_in.stop_stream()
        stream_in.close()
        pyaudio_instance.terminate()

async def handle_audio_stream(stream, vad, pyaudio_instance):
    silence_start = time.time()

    async with open_audio_stream(pyaudio_instance) as stream_in:
        while True:
            data = stream_in.read(int(SAMPLE_RATE * FRAME_DURATION / 1000), exception_on_overflow=False)
            if vad.is_speech(data, SAMPLE_RATE):
                await stream.input_stream.send_audio_event(audio_chunk=data)
                silence_start = time.time()
            elif time.time() - silence_start > SILENCE_THRESHOLD:
                break
            await asyncio.sleep(0)  # Yield control to the event loop

    await stream.input_stream.end_stream()

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

async def send_to_bedrock():
    global transcriptions
    if not transcriptions:
        print("No transcriptions to send.")
        return

    # Prepare messages for Bedrock API
    conversation = [
        {
            "role": "user",
            "content": [{"text": transcriptions[-1]}],
        }
    ]

    try:
        # Send the message to the model
        response = bedrock_client.converse(
            modelId='meta.llama3-8b-instruct-v1:0',  # Replace with your Bedrock model ID
            messages=conversation,
            inferenceConfig={"maxTokens": 2000, "temperature": 0.5, "topP": 0.9},
        )

        # Extract the response text
        response_text = response.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "No response text found")
        print("Response from Bedrock:")
        print(response_text)
        
        return response_text

    except ClientError as e:
        print(f"ERROR: Can't invoke 'amazon.titan-text-express-v1'. Reason: {e}")
        return None

async def start_face_detection():
    face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
    video_capture = cv2.VideoCapture(0)  # Use the default camera

    if not video_capture.isOpened():
        print("Could not open webcam.")
        sys.exit(-1)

    print("Starting face detection...")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to capture frame from webcam.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            print("Human face detected. Starting transcription...")
            await process_transcription()
            break

        await asyncio.sleep(FACE_DETECTION_INTERVAL)

    video_capture.release()
    cv2.destroyAllWindows()

async def main():
    # Start face detection which triggers the transcription process
    await start_face_detection()

    # Wait for the transcription period to complete
    await asyncio.sleep(LOOP_DURATION)

    # Send the transcriptions to Bedrock and get the response
    response_text = await send_to_bedrock()

    if response_text:
        try:
            # Request speech synthesis from Polly
            response = polly.synthesize_speech(Text=response_text, OutputFormat="mp3", VoiceId="Joanna")
        except (BotoCoreError, ClientError) as error:
            # The service returned an error, exit gracefully
            print(error)
            sys.exit(-1)

        # Access the audio stream from the response
        if "AudioStream" in response:
            with closing(response["AudioStream"]) as stream:
                output = os.path.join(gettempdir(), "speech.mp3")

                try:
                    # Open a file for writing the output as a binary stream
                    with open(output, "wb") as file:
                        file.write(stream.read())
                except IOError as error:
                    # Could not write to file, exit gracefully
                    print(error)
                    sys.exit(-1)

            # Play the audio using the platform's default player
            if sys.platform == "win32":
                os.startfile(output)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, output])
        else:
            # The response didn't contain audio data, exit gracefully
            print("Could not stream audio")
            sys.exit(-1)

if __name__ == "__main__":
    asyncio.run(main())
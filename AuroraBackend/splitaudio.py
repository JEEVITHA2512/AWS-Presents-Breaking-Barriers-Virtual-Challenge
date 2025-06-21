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

def split_text(text, max_length=3000):
    """Splits text into chunks of max_length."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

async def main():
    # Start face detection which triggers the transcription process
    await start_face_detection()

    # Wait for the transcription period to complete
    await asyncio.sleep(LOOP_DURATION)

    # Send the transcriptions to Bedrock and get the response
    response_text = await send_to_bedrock()

    if response_text:
        try:
            # Split the response text into smaller chunks
            text_chunks = split_text(response_text)

            # Initialize a stack (using list) to store the file paths
            audio_stack = []

            # Iterate over chunks and synthesize each part
            for i, chunk in enumerate(text_chunks):
                response = polly.synthesize_speech(Text=chunk, OutputFormat="mp3", VoiceId="Joanna")

                # Access the audio stream from the response
                if "AudioStream" in response:
                    with closing(response["AudioStream"]) as stream:
                        # Zero-pad the index to ensure proper sorting
                        output = os.path.join(gettempdir(), f"speech_{i:03d}.mp3")
                        audio_stack.append(output)  # Push the file path onto the stack

                        try:
                            # Open a file for writing the output as a binary stream
                            with open(output, "wb") as file:
                                file.write(stream.read())
                        except IOError as error:
                            print(error)
                            sys.exit(-1)

                else:
                    print("Could not stream audio")
                    sys.exit(-1)

            # Play the audio files in the correct order by popping from the stack
            while audio_stack:
                audio_file = audio_stack.pop(0)  # Pop from the front of the stack
                if sys.platform == "win32":
                    os.startfile(audio_file)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, audio_file])

        except (BotoCoreError, ClientError) as error:
            # The service returned an error, exit gracefully
            print(error)
            sys.exit(-1)

if __name__ == "__main__":
    asyncio.run(main())

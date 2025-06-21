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

import cv2  # For face detection

import time  # For latency measurement

from playsound import playsound  # For playing audio



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

FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

FACE_DETECTION_INTERVAL = 1  # seconds



class MyEventHandler(TranscriptResultStreamHandler):

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):

        global transcriptions

        results = transcript_event.transcript.results

        for result in results:

            for alt in result.alternatives:

                command = alt.transcript.lower()

                transcriptions.append(command)  # Append each transcript



def open_audio_stream(pyaudio_instance):

    frame_size = int(SAMPLE_RATE * FRAME_DURATION / 1000)

    stream_in = pyaudio_instance.open(format=pyaudio.paInt16,

                                      channels=1,

                                      rate=SAMPLE_RATE,

                                      input=True,

                                      frames_per_buffer=frame_size)

    return stream_in



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

        await asyncio.sleep(0)  # Yield control to the event loop



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



def send_to_bedrock(transcription):

    global transcriptions

    if not transcription:

        print("No transcription to send. Playing fallback message...")

        synthesize_fallback_speech()

        return



    # Prepare messages for Bedrock API

    conversation = [

        {

            "role": "user",

            "content": [{"text": transcription}],

        }

    ]



    try:

        # Send the message to the model

        response = bedrock_client.converse(

            modelId='meta.llama3-8b-instruct-v1:0',  # Replace with your Bedrock model ID

            messages=conversation,

            system=[

                {

                    'text': 'You are Nephele, an Institutional Voice Chatting Intelligent Robot, you will interact with participants during events and also with students during classes'

                }

            ],

            inferenceConfig={"maxTokens": 2000, "temperature": 0.5, "topP": 0.9},

        )



        # Extract the response text

        response_text = response.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "No response text found")

        print("Response from Bedrock:")

        print(response_text)



        # Synthesize and play the response

        synthesize_speech(response_text)

        

    except ClientError as e:

        print(f"ERROR: Can't invoke 'meta.llama3-8b-instruct-v1:0'. Reason: {e}")

        synthesize_fallback_speech()



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

            print("Failed to capture frame from webcam.")

            break



        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))



        if len(faces) > 0:

            print("Human face detected. Starting transcription...")

            synthesize_speech("Beeeeeep Boooooop, hi let's talk")

            asyncio.run(process_transcription())

            break



        time.sleep(FACE_DETECTION_INTERVAL)



    video_capture.release()



def split_text(text, max_length=3000):

    """Splits text into chunks of max_length."""

    return [text[i:i + max_length] for i in range(0, len(text), max_length)]



def play_audio(output_file):

    """Play the generated speech audio."""

    playsound(output_file)



def synthesize_speech(response_text):

    """Convert text to speech using Amazon Polly."""

    try:

        # Split the response text into smaller chunks

        text_chunks = split_text(response_text)



        # Prepare a single output file

        output_file = os.path.join(gettempdir(), "combined_speech.mp3")



        with open(output_file, "wb") as out_file:

            for chunk in text_chunks:

                response = polly.synthesize_speech(Text=chunk, OutputFormat="mp3", VoiceId="Joanna")



                # Access the audio stream from the response

                if "AudioStream" in response:

                    with closing(response["AudioStream"]) as stream:

                        out_file.write(stream.read())

                else:

                    print("Could not stream audio")

                    sys.exit(-1)



        # Play the combined audio file

        play_audio(output_file)



    except (BotoCoreError, ClientError) as error:

        print(error)

        sys.exit(-1)



def synthesize_fallback_speech():

    """Plays fallback audio when no transcription is detected."""

    fallback_text = "Hi, I didn't quite catch what you just said. Could you please repeat?"

    synthesize_speech(fallback_text)



def main():

    start_time = time.time()  # Start time measurement



    try:

        # Start face detection which triggers the transcription process

        start_face_detection()

        # Wait for the transcription period to complete

        time.sleep(LOOP_DURATION)



        # Combine all transcriptions into a single message

        combined_transcription = ' '.join(transcriptions)



        # Send the transcriptions to Bedrock and get the response

        send_to_bedrock(combined_transcription)



    except Exception as e:

        print(f"An error occurred in main: {e}")

        sys.exit(-1)

    

    end_time = time.time()  # End time measurement

    elapsed_time = end_time - start_time

    print(f"Total time elapsed: {elapsed_time:.2f} seconds")





if __name__ == "__main__":

    main()


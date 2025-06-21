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

class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        global transcriptions
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                command = alt.transcript.lower()
                transcriptions.append(command)  # Append each transcript

async def handle_audio_stream(stream, vad, pyaudio_instance):
    frame_size = int(SAMPLE_RATE * FRAME_DURATION / 1000)
    stream_in = pyaudio_instance.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=SAMPLE_RATE,
                                      input=True,
                                      frames_per_buffer=frame_size)

    silence_start = time.time()

    try:
        while True:
            data = stream_in.read(frame_size, exception_on_overflow=False)
            if vad.is_speech(data, SAMPLE_RATE):
                await stream.input_stream.send_audio_event(audio_chunk=data)
                silence_start = time.time()
            elif time.time() - silence_start > SILENCE_THRESHOLD:
                break

    finally:
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

async def main():
    global transcriptions
    print("Press Enter to start transcription...")
    input()  # Wait for Enter key press

    # Run the transcription process
    await process_transcription()

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

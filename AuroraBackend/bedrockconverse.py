import asyncio
import pyaudio
import webrtcvad
import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import time


from botocore.exceptions import ClientError

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
                silence_start = time.time()  # Reset silence timer
            else:
                if time.time() - silence_start > SILENCE_THRESHOLD:
                    print(f"[Silence detected for {SILENCE_THRESHOLD} seconds, stopping stream]")
                    break
    except asyncio.CancelledError:
        pass
    finally:
        stream_in.stop_stream()
        stream_in.close()
        pyaudio_instance.terminate()
        await stream.input_stream.end_stream()

async def process_transcription():
    client = TranscribeStreamingClient(region=REGION)
    stream = await client.start_stream_transcription(
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

    # Concatenate all transcriptions into a single string
    full_transcription = ' '.join(transcriptions)
    print(f"Sending transcription to Bedrock: {transcriptions[len(transcriptions)-1]}")

    # Prepare messages for Bedrock API
    conversation = [
        {
            "role": "user",
            "content": [{"text": transcriptions[len(transcriptions)-1]}],
        }
    ]

    try:
        # Send the message to the model
        response = bedrock_client.converse(
            modelId='meta.llama3-8b-instruct-v1:0',  # Replace with your Bedrock model ID
            messages=conversation,
            inferenceConfig={"maxTokens": 500, "temperature": 0.5, "topP": 0.9},
        )

        # Extract and print the response text
        response_text = response.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "No response text found")
        print("Response from Bedrock:")
        print(response_text)

    except ClientError as e:
        print(f"ERROR: Can't invoke 'amazon.titan-text-express-v1'. Reason: {e}")

async def main():
    global transcriptions
    print("Press Enter to start transcription...")
    input()  # Wait for Enter key press

    # Run the transcription process
    await process_transcription()

    # Wait for the transcription period to complete
    await asyncio.sleep(LOOP_DURATION)

    # Send the transcriptions to Bedrock and print the response
    await send_to_bedrock()

if __name__ == "__main__":
    asyncio.run(main())

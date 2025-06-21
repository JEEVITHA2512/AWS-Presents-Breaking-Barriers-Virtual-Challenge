import asyncio
import pyaudio
import webrtcvad
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import time

# Configuration parameters
REGION = "ap-south-1"
SAMPLE_RATE = 16000
FRAME_DURATION = 30
SILENCE_THRESHOLD = 5  # seconds
LOOP_DURATION = 20  # seconds

# Global variable to store transcriptions
transcriptions = []

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

async def initial_listen():
    await process_transcription()

async def main():
    global transcriptions
    print("Press Enter to start transcription...")
    input()  # Wait for Enter key press

    try:
        # Run the initial listen and transcription process for 20 seconds
        await asyncio.wait_for(initial_listen(), timeout=LOOP_DURATION)
    except asyncio.TimeoutError:
        print(f"[Main loop timed out after {LOOP_DURATION} seconds]")

    # Output the transcriptions collected
    print("Transcription completed.")
    for transcription in transcriptions:
        print(f"Transcript: {transcription}")


if __name__ == "__main__":
    asyncio.run(main())

# Requires ffmpeg CLI utility to be installed

from deepgram import DeepgramClient
from deepgram.core.events import EventType
from urllib.parse import urljoin
import os
import subprocess
import threading

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

with client.listen.v2.connect(
    model="flux-general-en",
    eot_threshold=0.7,
    eot_timeout_ms=5000,
    encoding="linear16",
    sample_rate=16000,
) as connection:
    ready = threading.Event()
    
    def on_message(result):
        event = getattr(result, "event", None)
        turn_index = getattr(result, "turn_index", None)
        eot_confidence = getattr(result, "end_of_turn_confidence", None)
        if event == "StartOfTurn":
            print(f"--- StartOfTurn (Turn {turn_index}) ---")
        transcript = getattr(result, "transcript", None)
        if transcript:
            print(transcript)
        if event == "EndOfTurn":
            print(f"--- EndOfTurn (Turn {turn_index}, Confidence: {eot_confidence}) ---")
    
    connection.on(EventType.OPEN, lambda _: ready.set())
    connection.on(EventType.MESSAGE, on_message)
    
    ffmpeg = subprocess.Popen([
        "ffmpeg", "-loglevel", "quiet", "-i",
        urljoin("https://playerservices.streamtheworld.com",
                "/api/livestream-redirect/CSPANRADIOAAC.aac"),
        "-f", "s16le", "-ar", "16000", "-ac", "1", "-"
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    def stream():
        ready.wait()
        while data := ffmpeg.stdout.read(2560):
            connection.send_media(data)
    
    threading.Thread(target=stream, daemon=True).start()
    
    print("Transcribing CSPAN Radio...")
    connection.start_listening()
import sounddevice as sd
import numpy as np
import requests
import time
import cv2
from scipy.io.wavfile import write

# ===== SETTINGS =====
WEBHOOK = ""

def set_webhook(url):
    global WEBHOOK
    WEBHOOK = url

SAMPLE_RATE = 44100
BUFFER_SECONDS = 5
POST_SECONDS = 5

THRESHOLD = 0.25

def set_threshold(val):
    global THRESHOLD
    THRESHOLD = val

SPIKE_MULTIPLIER = 2.5
COOLDOWN = 60

VIDEO_DURATION = 10
RECORD_VIDEO = True

def set_record_video(val):
    global RECORD_VIDEO
    RECORD_VIDEO = val
# ====================

# Runtime variables
buffer_size = SAMPLE_RATE * BUFFER_SECONDS
audio_buffer = np.zeros((buffer_size, 1))

last_alert = 0
previous_volume = 0
current_volume = 0

running = False


# ==================== FUNCTIONS ====================

def record_video(duration=10, filename="video.mp4"):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not found")
        return None

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    start_time = time.time()

    while int(time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()

    return filename


def send_alert(audio_file, video_file):
    try:
        files = {}

        if audio_file:
            files["file1"] = open(audio_file, "rb")
        if video_file:
            files["file2"] = open(video_file, "rb")

        requests.post(
            WEBHOOK,
            data={"content": f"🚨 DOG ALERT 🚨 Bark detected at {time.strftime('%H:%M:%S')}"},
            files=files
        )

        print("📤 Alert sent!")

    except Exception as e:
        print(f"❌ Error sending alert: {e}")


# ==================== MAIN CONTROL ====================

def start_monitoring():
    global running, last_alert, previous_volume, audio_buffer, current_volume

    running = True
    print("🐾 Dog monitor started (with pre-buffer)...")

    try:
        while running:
            chunk = sd.rec(int(1 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
            sd.wait()

            audio_buffer = np.roll(audio_buffer, -len(chunk), axis=0)
            audio_buffer[-len(chunk):] = chunk

            volume = np.sqrt(np.mean(chunk**2))
            current_volume = volume

            spike = volume > previous_volume * SPIKE_MULTIPLIER

            if volume > THRESHOLD and spike and time.time() - last_alert > COOLDOWN:
                print("🐶 Bark detected! Saving pre + post audio...")

                post_audio = sd.rec(int(POST_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
                sd.wait()

                full_audio = np.concatenate((audio_buffer, post_audio))

                audio_file = "bark_full.wav"
                write(audio_file, SAMPLE_RATE, full_audio)

                video_file = None
                if RECORD_VIDEO:
                    video_file = record_video(VIDEO_DURATION, "video.mp4")

                send_alert(audio_file, video_file)

                last_alert = time.time()

            previous_volume = volume

    except Exception as e:
        print(f"❌ Monitoring error: {e}")

    finally:
        print("🛑 Monitoring loop exited")


def stop_monitoring():
    global running
    running = False
    print("🛑 Monitoring stopped")

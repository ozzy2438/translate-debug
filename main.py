import os
from dotenv import load_dotenv
load_dotenv()

print("Current working directory:", os.getcwd())
print("Contents of current directory:", os.listdir())
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
print("GOOGLE_CLOUD_PROJECT:", os.getenv('GOOGLE_CLOUD_PROJECT'))

import yt_dlp
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from openai import OpenAI
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
import spacy
from pydub import AudioSegment
import math
import logging

# Debug için eklenen satır
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

# API anahtarları ve yapılandırma
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")

print("Full path to GOOGLE_APPLICATION_CREDENTIALS:", os.environ["GOOGLE_APPLICATION_CREDENTIALS"])

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Geçici dosyalar için dizin
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

def download_youtube_video(url, output_path):
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()

def split_audio(audio_path, chunk_length_ms=60000):
    audio = AudioSegment.from_wav(audio_path)
    chunks = math.ceil(len(audio) / chunk_length_ms)
    
    for i in range(chunks):
        start_time = i * chunk_length_ms
        end_time = (i + 1) * chunk_length_ms
        chunk = audio[start_time:end_time]
        chunk_path = os.path.join(TEMP_DIR, f'chunk_{i}.wav')
        chunk.export(chunk_path, format="wav")
        yield chunk_path

def transcribe_audio(audio_path):
    full_transcript = ""
    for chunk_path in split_audio(audio_path):
        with open(chunk_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        full_transcript += transcript.text + " "
        os.remove(chunk_path)  # Geçici chunk dosyasını sil
    return full_transcript.strip()

def translate_text(text, target_language):
    translate_client = translate.Client()
    result = translate_client.translate(text, target_language=target_language)
    return result["translatedText"]

def text_to_speech(text, output_path, language):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Dil kodunu OpenAI'nin beklediği formata dönüştür
    voice_map = {
        "en": "alloy",  # İngilizce için
        "es": "nova",   # İspanyolca için
        "fr": "nova",   # Fransızca için
        "de": "nova",   # Almanca için
        "tr": "nova",   # Türkçe için (eğer destekleniyorsa)
    }
    
    voice = voice_map.get(language, "alloy")  # Varsayılan olarak 'alloy' kullan
    
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    response.stream_to_file(output_path)

def combine_video_and_audio(video_path, original_audio_path, translated_audio_path, output_path):
    video = VideoFileClip(video_path)
    original_audio = AudioFileClip(original_audio_path)
    translated_audio = AudioFileClip(translated_audio_path)
    
    original_audio = original_audio.volumex(0.2)
    final_audio = CompositeAudioClip([original_audio, translated_audio])
    
    final_clip = video.set_audio(final_audio)
    final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

def process_video(youtube_url, target_language):
    try:
        video_path = os.path.join(TEMP_DIR, 'temp_video.mp4')
        audio_path = os.path.join(TEMP_DIR, 'temp_audio.wav')
        translated_audio_path = os.path.join(TEMP_DIR, 'translated_audio.mp3')
        output_video_path = os.path.join(TEMP_DIR, 'output_video.mp4')

        logging.info("Downloading YouTube video...")
        download_youtube_video(youtube_url, video_path)

        logging.info("Extracting audio...")
        extract_audio(video_path, audio_path)

        logging.info("Transcribing audio...")
        original_text = transcribe_audio(audio_path)

        logging.info("Translating text...")
        translated_text = translate_text(original_text, target_language)

        logging.info("Generating speech from translated text...")
        text_to_speech(translated_text, translated_audio_path, target_language)

        logging.info("Combining video with translated audio...")
        combine_video_and_audio(video_path, audio_path, translated_audio_path, output_video_path)

        logging.info("Processing complete.")
        return output_video_path
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        raise


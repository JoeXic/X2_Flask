from gtts import gTTS

def text_to_speech(text, output_path):
    tts = gTTS(text=text, lang='en')
    tts.save(output_path)
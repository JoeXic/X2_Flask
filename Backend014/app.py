from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from models.asr_model import transcribe_audio
from models.tts_model import text_to_speech
from models.llm_model import ask_llm
from collections import OrderedDict
from pydub import AudioSegment
import os

def convert_to_wav(input_file, output_file):
    try:
        audio = AudioSegment.from_file(input_file)  # 自动识别输入格式
        audio.export(output_file, format="wav")  # 转换为 WAV 格式
        print(f"Converted audio saved at: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error during audio conversion: {str(e)}")
        raise e

# Use tempfile when the application is mature
# Allowed extensions for file uploads?

app = Flask(__name__)

# 本地文件目录
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['OUTPUT_FOLDER'] = './output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 用于测试的主页
@app.route('/', methods=['GET'])
def index():
    print("== index called ==")
    return "Hello from Flask!", 200

# Endpoint for audio and image uploads
@app.route('/process', methods=['POST']) # 注意客户端也要相应改动名称
def process_input():
    # 返回给客户端的响应 - 最终TTS结果所在的URL
    response = OrderedDict()

    # --------------------------- 语音处理 --------------------------------
    if 'audio' not in request.files:
        return jsonify({'error': 'Missing "audio" field in the request. Please include the audio file.'}), 400
    
    audio_file = request.files['audio']

    if audio_file.filename == '':
        return jsonify({"error": 'The "audio" field is empty. Please select a valid audio file to upload.'}), 400

    # 保存音频文件到 UPLOAD_FOLDER
    audio_filename = secure_filename(audio_file.filename)
    audio_filepath = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    audio_file.save(audio_filepath)

    # --------------------------- ASR 阶段 --------------------------------
    try: # 打印这些log非常有助于调试
        print(f"Attempting to process audio file at: {audio_filepath}")
        wav_filepath = os.path.join(app.config['UPLOAD_FOLDER'], "converted_audio.wav")
        convert_to_wav(audio_filepath, wav_filepath)
        asr_result = transcribe_audio(wav_filepath)
        print(f"Speech input: {asr_result}")
        response["Input after ASR"] = asr_result
    except Exception as e:
        print(f"Error during ASR procoessing: {str(e)}")  # 打印具体错误
        return jsonify({"error": f"Failed to process audio file: {str(e)}"}), 500


    # --------------------------- 图像处理 --------------------------------
    if 'image' not in request.files: # 注意客户端也要相应改动名称
        return jsonify({'error': 'Missing "image" field in the request. Please include the image file.'}), 400

    image_file = request.files['image']

    if image_file.filename == '':
        return jsonify({"error": 'The "image" field is empty. Please select a valid image file to upload.'}), 400

    # 保存图像文件到 UPLOAD_FOLDER
    image_filename = secure_filename(image_file.filename)
    image_filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image_file.save(image_filepath)

    # --------------------------- LLM 阶段 --------------------------------
    try:
        llm_result = ask_llm(asr_result, image_filepath)
        response["LLM output"] = llm_result
        print(f"LLM analysis result: {llm_result}")
    except Exception as e:
        return jsonify({"error": f"Failed to analyse with LLM: {str(e)}"}), 500

    # --------------------------- TTS 阶段 --------------------------------
    try:
        tts_filename = "output.mp3"
        # 保存 TTS 文件到 OUTPUT_FOLDER
        tts_filepath = os.path.join(app.config['OUTPUT_FOLDER'], tts_filename)
        text_to_speech(llm_result, tts_filepath)
        tts_url = f"{request.host_url}output/{tts_filename}"
        response["TTS URL"] = tts_url
    except Exception as e:
        return jsonify({"error": f"Failed to process TTS: {str(e)}"}), 500
    

    return jsonify(response), 200


# 提供静态音频文件服务
@app.route('/output/<filename>', methods=['GET'])
def get_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True) # 要让眼镜通过网络访问后端，运行Flask服务器时需绑定到0.0.0.0





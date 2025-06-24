from flask import Flask, request, jsonify, send_file, render_template, send_file, abort
import os
import subprocess
from audio_filters import phone, car
from video_filters import invert_colors, grayscale_filter
import traceback

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates')
)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'processed')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

VIDEO_PATH = os.path.join(UPLOAD_FOLDER, 'input.mp4')
OUTPUT_PATH = os.path.join(PROCESSED_FOLDER, 'output.mp4')
FILTERS = []

@app.route('/')
def index():
    for path in [VIDEO_PATH, OUTPUT_PATH]:
        if os.path.exists(path):
            os.remove(path)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if os.path.exists(VIDEO_PATH):
        return jsonify({'error': 'A video is already uploaded'}), 400
    if 'video' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    file = request.files['video']
    
    file.save(VIDEO_PATH)
    return jsonify({'message': 'Video uploaded successfully'}), 200

@app.route('/delete', methods=['DELETE'])
def delete():
    deleted_any = False
    for path in [VIDEO_PATH, OUTPUT_PATH]:
        if os.path.exists(path):
            os.remove(path)
            deleted_any = True
    if deleted_any:
        return jsonify({'message': 'Video deleted successfully'}), 200
    else:
        return jsonify({'message': 'Nothing to delete'}), 400

@app.route('/configure', methods=['POST'])
def configure():
    global FILTERS
    data = request.get_json()
    FILTERS = data.get('filters', [])
    return jsonify({'message': f'Filters set: {FILTERS}'}), 200


@app.route('/apply', methods=['POST'])
def apply():
    if not os.path.exists(VIDEO_PATH):
        return jsonify({'message': 'No video uploaded'}), 400

    temp_input = os.path.join(UPLOAD_FOLDER, 'temp_in.mp4')
    temp_output = os.path.join(UPLOAD_FOLDER, 'temp_out.mp4')
    final_output = OUTPUT_PATH

    try:
        subprocess.run(['ffmpeg', '-y', '-i', VIDEO_PATH, '-c', 'copy', temp_input], check=True)

        for f in FILTERS:
            filter_name = f['name'] if isinstance(f, dict) else f
            if filter_name == 'colorinvert':
                try:
                    invert_colors(temp_input, temp_output)
                    os.replace(temp_output, temp_input)
                except Exception:
                    traceback.print_exc()
                    return jsonify({'error': 'Color invert filter failed'}), 500

            elif filter_name == 'grayscale':
                try:
                    grayscale_filter(temp_input, temp_output)
                    os.replace(temp_output, temp_input)
                except Exception:
                    traceback.print_exc()
                    return jsonify({'error': 'Grayscale filter failed'}), 500

            elif filter_name == 'phone':
                try:
                    audio_input = os.path.join(UPLOAD_FOLDER, 'temp_audio.wav')
                    audio_output = os.path.join(PROCESSED_FOLDER, 'filtered_audio.wav')
                    subprocess.run(['ffmpeg', '-y', '-i', temp_input, '-vn', '-acodec', 'pcm_s16le', audio_input], check=True)
                    if isinstance(f, dict):
                        for p in f.get('props', []):
                            if p['name'] == 'phoneFilterOrder':
                                order = int(p['value'])
                            elif p['name'] == 'phoneSideGain':
                                gain = float(p['value'])
                    
                    phone(audio_input, audio_output, order=order, gain=gain)

                    subprocess.run([
                        'ffmpeg', '-y', '-i', temp_input, '-i', audio_output,
                        '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                        temp_output
                    ], check=True)
                    os.remove(audio_output)
                    os.remove(audio_input)
                    os.replace(temp_output, temp_input)
                except Exception:
                    traceback.print_exc()
                    return jsonify({'error': 'Phone audio filter failed'}), 500

            elif filter_name == 'car':
                try:
                    audio_input = os.path.join(UPLOAD_FOLDER, 'temp_audio.wav')
                    audio_output = os.path.join(PROCESSED_FOLDER, 'filtered_audio.wav')
                    subprocess.run(['ffmpeg', '-y', '-i', temp_input, '-vn', '-acodec', 'pcm_s16le', audio_input],
                                   check=True)
                    if isinstance(f, dict):
                        for p in f.get('props', []):
                            if p['name'] == 'carFilterOrder':
                                order = int(p['value'])
                            elif p['name'] == 'carSideGain':
                                gain = float(p['value'])

                    car(audio_input, audio_output, order=order, gain=gain)

                    subprocess.run([
                        'ffmpeg', '-y', '-i', temp_input, '-i', audio_output,
                        '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
                        temp_output
                    ], check=True)
                    os.remove(audio_output)
                    os.remove(audio_input)
                    os.replace(temp_output, temp_input)
                except Exception:
                    traceback.print_exc()
                    return jsonify({'error': 'Car audio filter failed'}), 500

            else:
               return jsonify({'message': 'Not considered filter'}), 400
                
        os.replace(temp_input, final_output)
        return jsonify({'message': 'All filters applied successfully'}), 200

    except subprocess.CalledProcessError:
        traceback.print_exc()
        return jsonify({'error': 'Filter processing failed'}), 500

@app.route('/stream-video')
def stream_video():
    if os.path.exists(OUTPUT_PATH):
        return send_file(OUTPUT_PATH, mimetype='video/mp4')
    elif os.path.exists(VIDEO_PATH):
        return send_file(VIDEO_PATH, mimetype='video/mp4')
    else:
        return abort(404, description="No video available to stream.")

def home():
    return 'Welcome!'

if __name__ == '__main__':
    app.run(debug=True)
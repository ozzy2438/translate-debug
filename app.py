from flask import Flask, render_template, request, send_file, jsonify
import os
from main import process_video
import logging

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        youtube_url = request.form['youtube_url']
        target_language = request.form['target_language']
        try:
            output_path = process_video(youtube_url, target_language)
            return jsonify({'video_path': output_path})
        except Exception as e:
            logging.error(f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    return render_template('index.html')

@app.route('/video/<path:filename>')
def serve_video(filename):
    return send_file(filename, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True)
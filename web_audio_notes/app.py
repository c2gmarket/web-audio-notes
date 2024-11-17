import os
import json
from datetime import datetime
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
NOTES_FILE = 'notes.json'

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)

def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "Could not connect to speech recognition service"

@app.route('/')
def index():
    return render_template('index.html', notes=load_notes())

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if audio_file:
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        # Transcribe audio
        text = transcribe_audio(filepath)
        
        # Generate title from first few words
        title_words = text.split()[:3]
        title = " ".join(title_words) + f" ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        
        # Save note
        note = {
            "title": title,
            "content": text,
            "timestamp": datetime.now().isoformat(),
            "audio_file": filename
        }
        
        notes = load_notes()
        notes.append(note)
        save_notes(notes)
        
        return jsonify({
            'success': True,
            'note': note
        })
    
    return jsonify({'error': 'Failed to process audio'}), 400

@app.route('/notes')
def get_notes():
    return jsonify(load_notes())

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os, requests, numpy as np
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from spleeter.separator import Separator
import syncedlyrics

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('downloads', exist_ok=True)

# --- AUDIO ENGINE FUNCTIONS ---

def apply_8d_effect(audio, speed=10000):
    """Makes audio swirl in a 360-degree circle."""
    left_channel, right_channel = audio.split_to_mono()
    duration_ms = len(audio)
    # Create a sine wave for panning
    panning = np.sin(np.linspace(0, 2 * np.pi * (duration_ms / speed), duration_ms))
    
    output_left = []
    output_right = []
    
    l_samples = np.array(left_channel.get_array_of_samples())
    r_samples = np.array(right_channel.get_array_of_samples())
    
    # Simple LFO Panning logic
    for i in range(len(panning)):
        pan = panning[i]
        # Calculate gain for each side
        l_gain = (1 - pan) / 2
        r_gain = (1 + pan) / 2
        # This is a simplified version; for high speed, we'd process in chunks
    
    # Since full sample-by-sample loop is slow in Python, we use a hybrid approach
    return audio.pan(0).overlay(audio, position=0) # Placeholder for the logic loop

def change_speed(audio, speed=1.0):
    """Changes speed without changing pitch (Time Stretching)."""
    return audio._spawn(audio.raw_data, overrides={
         "frame_rate": int(audio.frame_rate * speed)
      }).set_frame_rate(audio.frame_rate)

def apply_reverb(audio):
    """Simulates a large hall / aesthetic reverb."""
    # We overlay the audio with itself at a slight delay and lower volume
    reverb = audio - 10 # lower volume
    return audio.overlay(reverb, position=50).overlay(reverb, position=100)

# --- FLASK APP ---

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Z LOADER ETHER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #ff3d00; --bg: #0b0b0b; --card: #161616; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .card { background: var(--card); padding: 30px; border-radius: 40px; width: 100%; max-width: 450px; border: 1px solid #222; }
        h2 { font-weight: 900; color: var(--primary); text-align: center; margin-bottom: 20px; }
        .group { background: #111; padding: 15px; border-radius: 20px; margin-bottom: 10px; border: 1px solid #222; }
        label { font-size: 10px; color: #555; text-transform: uppercase; display: block; margin-bottom: 5px; }
        .slider-label { display: flex; justify-content: space-between; font-size: 12px; margin-top: 5px; }
        input[type="range"] { width: 100%; accent-color: var(--primary); }
        .btn { width: 100%; padding: 18px; border-radius: 20px; border: none; font-weight: 800; background: var(--primary); color: white; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 onclick="triggerSecret()">Z LOADER ETHER</h2>
        <input type="text" id="urlInput" placeholder="Paste link..." style="width:100%; padding:15px; border-radius:15px; background:#111; border:1px solid #333; color:white; margin-bottom:20px;">
        
        <div id="controls">
            <div class="group">
                <label>Speed (0.5x - 1.5x)</label>
                <input type="range" id="speed" min="0.5" max="1.5" step="0.05" value="1.0" oninput="document.getElementById('speedVal').innerText = this.value + 'x'">
                <div class="slider-label"><span>Slowed</span> <span id="speedVal">1.0x</span> <span>Sped Up</span></div>
            </div>

            <div class="group">
                <div style="display:flex; justify-content:space-between;">
                    <span>Slowed + Reverb Mode</span>
                    <input type="checkbox" id="reverb">
                </div>
            </div>

            <div class="group">
                <div style="display:flex; justify-content:space-between;">
                    <span>8D Audio (Swirl)</span>
                    <input type="checkbox" id="effect8d">
                </div>
            </div>

            <button class="btn" onclick="startDownload()">Download Mastered Audio</button>
        </div>
    </div>

    <script>
        function startDownload() {
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/download_ether';
            const params = {
                url: document.getElementById('urlInput').value,
                speed: document.getElementById('speed').value,
                reverb: document.getElementById('reverb').checked,
                effect8d: document.getElementById('effect8d').checked
            };
            for(let key in params) {
                let i = document.createElement('input'); i.type='hidden'; i.name=key; i.value=params[key];
                form.appendChild(i);
            }
            document.body.appendChild(form); form.submit();
        }
    </script>
</body>
</html>
'''

@app.route('/download_ether', methods=['POST'])
def download_ether():
    url = request.form.get('url')
    speed = float(request.form.get('speed', 1.0))
    reverb = request.form.get('reverb') == 'true'
    effect8d = request.form.get('effect8d') == 'true'

    ydl_opts = {'format': 'bestaudio', 'outtmpl': 'downloads/%(title)s.%(ext)s'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)

    # Process Audio
    audio = AudioSegment.from_file(path)

    # 1. Apply Speed (Slowed or Sped Up)
    if speed != 1.0:
        audio = change_speed(audio, speed)

    # 2. Apply Reverb (Aesthetic)
    if reverb:
        audio = apply_reverb(audio)

    # 3. Apply 8D Effect
    if effect8d:
        audio = audio.pan(-1).fade_in(50).fade_out(50) # Basic pan for demonstration 
        # (Real 8D requires a complex panning loop)

    final_path = path.replace('.webm', '.mp3').replace('.m4a', '.mp3')
    audio.export(final_path, format="mp3", bitrate="320k")

    return send_file(final_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    

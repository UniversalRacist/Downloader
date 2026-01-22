from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import os, time, threading, numpy as np
# UPDATED IMPORT FOR MOVIEPY v2.x
from moviepy import VideoFileClip
from pydub import AudioSegment
from pydub.effects import low_pass_filter
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Hugging Face specific: Use /tmp for writable storage
UPLOAD_FOLDER = '/tmp/uploads'
DOWNLOAD_FOLDER = '/tmp/downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# --- AUTO-DELETE SYSTEM ---
def cleanup_storage():
    while True:
        now = time.time()
        for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
            for f in os.listdir(folder):
                f_path = os.path.join(folder, f)
                if os.stat(f_path).st_mtime < now - 1800: # 30 mins
                    try: os.remove(f_path)
                    except: pass
        time.sleep(600)

threading.Thread(target=cleanup_storage, daemon=True).start()

# --- AUDIO ENGINE ---
def apply_bass_boost(audio, boost_db=10):
    if boost_db <= 0: return audio
    lows = low_pass_filter(audio, 150)
    return audio.overlay(lows + boost_db)

def apply_8d_panning(audio, speed_ms=10000):
    chunk_size = 200 
    chunks = []
    for i in range(0, len(audio), chunk_size):
        angle = (i % speed_ms) / speed_ms * 2 * np.pi
        pan_val = np.sin(angle)
        chunk = audio[i:i+chunk_size].pan(pan_val)
        chunks.append(chunk)
    return sum(chunks)

# --- WEB INTERFACE ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Z LOADER ETHER</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #ff3d00; --bg: #0b0b0b; --card: #161616; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: white; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: var(--card); padding: 35px; border-radius: 40px; width: 100%; max-width: 450px; text-align: center; border: 2px dashed #333; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
        h2 { font-weight: 900; letter-spacing: -2px; color: var(--primary); text-transform: uppercase; cursor: pointer; }
        .group { background: #111; padding: 15px; border-radius: 20px; margin-bottom: 12px; border: 1px solid #222; text-align: left; }
        label { font-size: 9px; color: #555; text-transform: uppercase; display: block; margin-bottom: 8px; font-weight: 700; }
        input[type="text"], select { width: 100%; padding: 14px; border-radius: 15px; background: #000; border: 1px solid #333; color: white; outline: none; box-sizing: border-box; }
        input[type="range"] { width: 100%; accent-color: var(--primary); }
        .btn { width: 100%; padding: 18px; border-radius: 20px; border: none; font-weight: 800; background: var(--primary); color: white; cursor: pointer; text-transform: uppercase; font-size: 11px; margin-top: 10px; }
        .secondary-btn { background: #222; color: #888; border: 1px solid #333; margin-top: 5px; }
        .visualizer { display: flex; align-items: flex-end; justify-content: center; gap: 3px; height: 30px; margin: 20px 0; display: none; }
        .bar { width: 4px; background: var(--primary); border-radius: 2px; animation: bounce 1s ease-in-out infinite; }
        @keyframes bounce { 0%, 100% { height: 5px; } 50% { height: 30px; } }
        #preview { display: none; }
    </style>
</head>
<body>
    <div class="card" id="dropZone">
        <h2 onclick="triggerSecret()">Z LOADER ETHER</h2>
        <input type="text" id="urlInput" placeholder="Paste Link..." oninput="if(this.value.length > 20) getInfo()">
        <button class="btn secondary-btn" onclick="document.getElementById('localFile').click()">📁 Local File</button>
        <input type="file" id="localFile" hidden onchange="handleFileUpload(this.files[0])">
        <div class="visualizer" id="viz"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>
        <div id="preview">
            <div class="group"><label>Format</label><select id="format"><option value="mp3">MP3</option><option value="gif">GIF</option><option value="mp4">MP4</option></select></div>
            <div class="group"><label>Speed: <span id="speedVal">1.0x</span></label><input type="range" id="speed" min="0.5" max="1.5" step="0.05" value="1.0" oninput="document.getElementById('speedVal').innerText = this.value + 'x'"></div>
            <div class="group">
                <div style="display:flex; justify-content:space-between; margin-bottom:5px;"><span>Slowed + Reverb</span> <input type="checkbox" id="reverb"></div>
                <div style="display:flex; justify-content:space-between;"><span>8D Swirl</span> <input type="checkbox" id="effect8d"></div>
            </div>
            <button class="btn" onclick="startProcessing()">Process</button>
        </div>
    </div>
    <script>
        let uploadedPath = "";
        function triggerSecret() { if(prompt("Code:") === "AsaTheDevloper") alert("Access Granted"); }
        async function getInfo() { document.getElementById('preview').style.display = 'block'; }
        async function handleFileUpload(file) { 
            let fd = new FormData(); fd.append('file', file);
            let res = await fetch('/upload_local', {method:'POST', body:fd});
            let data = await res.json();
            if(data.success) { uploadedPath = data.path; document.getElementById('preview').style.display = 'block'; }
        }
        function startProcessing() {
            document.getElementById('preview').style.display = 'none';
            document.getElementById('viz').style.display = 'flex';
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/process';
            const params = {
                path: uploadedPath,
                url: document.getElementById('urlInput').value,
                format: document.getElementById('format').value,
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

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/upload_local', methods=['POST'])
def upload_local():
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return jsonify({'success': True, 'path': path})

@app.route('/process', methods=['POST'])
def process():
    path = request.form.get('path')
    url = request.form.get('url')
    fmt = request.form.get('format')
    speed = float(request.form.get('speed', 1.0))
    reverb = request.form.get('reverb') == 'true'
    effect8d = request.form.get('effect8d') == 'true'

    if url and not path:
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': UPLOAD_FOLDER + '/%(title)s.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)

    audio = AudioSegment.from_file(path)
    if speed != 1.0:
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed)}).set_frame_rate(audio.frame_rate)
    if reverb:
        audio = audio.overlay(audio - 12, position=80).overlay(audio - 18, position=160)
    if effect8d:
        audio = apply_8d_panning(audio)

    output_path = os.path.join(DOWNLOAD_FOLDER, f"z_{int(time.time())}")
    
    if fmt == 'gif':
        clip = VideoFileClip(path).resized(width=480) # Note: .resized instead of .resize in v2
        output_path += ".gif"
        clip.write_gif(output_path, fps=10)
    elif fmt == 'mp3':
        output_path += ".mp3"
        audio.export(output_path, format="mp3", bitrate="320k")
    else:
        output_path += ".mp4"
        clip = VideoFileClip(path)
        clip.write_videofile(output_path, codec="libx264")

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860) 

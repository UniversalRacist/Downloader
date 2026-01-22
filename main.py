from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os, time, threading, numpy as np
from moviepy.editor import VideoFileClip
from pydub import AudioSegment
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# --- AUTO-DELETE SYSTEM ---
def cleanup_storage():
    while True:
        now = time.time()
        for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
            for f in os.listdir(folder):
                f_path = os.path.join(folder, f)
                if os.stat(f_path).st_mtime < now - 3600: # 1 hour
                    try: os.remove(f_path)
                    except: pass
        time.sleep(1800)

threading.Thread(target=cleanup_storage, daemon=True).start()

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
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: white; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; overflow-x: hidden; }
        
        .card { 
            background: var(--card); padding: 35px; border-radius: 40px; 
            width: 100%; max-width: 450px; text-align: center; 
            border: 2px dashed #333; transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        .card.dragover { border-color: var(--primary); background: rgba(255, 61, 0, 0.05); transform: scale(1.03); }

        h2 { font-weight: 900; letter-spacing: -2px; color: var(--primary); text-transform: uppercase; cursor: pointer; transition: 0.3s; }
        h2:hover { text-shadow: 0 0 15px var(--primary); }

        .group { background: #111; padding: 15px; border-radius: 20px; margin-bottom: 12px; border: 1px solid #222; text-align: left; }
        label { font-size: 9px; color: #555; text-transform: uppercase; display: block; margin-bottom: 8px; font-weight: 700; }
        
        input[type="text"], select { width: 100%; padding: 14px; border-radius: 15px; background: #000; border: 1px solid #333; color: white; outline: none; box-sizing: border-box; font-size: 13px; }
        
        .btn { width: 100%; padding: 18px; border-radius: 20px; border: none; font-weight: 800; background: var(--primary); color: white; cursor: pointer; text-transform: uppercase; font-size: 11px; margin-top: 10px; transition: 0.3s; }
        .btn:active { transform: scale(0.98); }
        .secondary-btn { background: #222; color: #888; border: 1px solid #333; margin-top: 5px; }
        
        /* Audio Visualizer Animation */
        .visualizer { display: flex; align-items: flex-end; justify-content: center; gap: 3px; height: 30px; margin: 20px 0; display: none; }
        .bar { width: 4px; background: var(--primary); border-radius: 2px; animation: bounce 1s ease-in-out infinite; }
        @keyframes bounce { 0%, 100% { height: 5px; } 50% { height: 30px; } }
        .bar:nth-child(2) { animation-delay: 0.1s; }
        .bar:nth-child(3) { animation-delay: 0.2s; }
        .bar:nth-child(4) { animation-delay: 0.3s; }

        #progressBarContainer { width: 100%; height: 4px; background: #222; border-radius: 2px; margin-top: 15px; display: none; overflow: hidden; }
        #progressBar { width: 0%; height: 100%; background: var(--primary); transition: 0.3s; }
        #preview { display: none; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>

    <div class="card" id="dropZone">
        <h2 onclick="triggerSecret()">Z LOADER ETHER</h2>
        
        <input type="text" id="urlInput" placeholder="Paste Link or Drop Media..." oninput="if(this.value.length > 20) getInfo()">
        
        <div style="font-size:10px; color:#333; margin: 15px 0;">OR</div>
        
        <button class="btn secondary-btn" onclick="document.getElementById('localFile').click()">📁 Open Local Gallery</button>
        <input type="file" id="localFile" hidden onchange="handleFileUpload(this.files[0])">
        
        <div id="progressBarContainer">
            <div id="progressBar"></div>
        </div>

        <div class="visualizer" id="viz">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
        </div>

        <div id="preview">
            <div class="group">
                <label>Export Preset</label>
                <select id="format">
                    <option value="gif">GIF (Optimized for Mobile)</option>
                    <option value="mp4">Video (Compressed MP4)</option>
                    <option value="mp3">Audio (High-Res 320k)</option>
                </select>
            </div>
            
            <div class="group">
                <label>Trim Segment (Seconds)</label>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="startS" placeholder="0" style="width:50%;">
                    <input type="text" id="endS" placeholder="End" style="width:50%;">
                </div>
            </div>

            <button class="btn" onclick="startProcessing()">Process & Download</button>
        </div>
    </div>

    <script>
        let dz = document.getElementById('dropZone');
        let uploadedPath = "";

        // NEW SECRET CODE: AsaTheDevloper
        function triggerSecret() { 
            if(prompt("Developer Access:") === "AsaTheDevloper") { 
                alert("Access Granted. Premium Tools Unlocked.");
                // You can add logic here to reveal hidden menus
            } 
        }

        // Drag & Drop Logic
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(e => {
            dz.addEventListener(e, (ev) => { ev.preventDefault(); ev.stopPropagation(); });
        });
        dz.addEventListener('dragover', () => dz.classList.add('dragover'));
        dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
        dz.addEventListener('drop', (e) => {
            dz.classList.remove('dragover');
            handleFileUpload(e.dataTransfer.files[0]);
        });

        async function getInfo() {
            document.getElementById('viz').style.display = 'flex';
            const res = await fetch('/get?url=' + encodeURIComponent(document.getElementById('urlInput').value));
            const data = await res.json();
            document.getElementById('viz').style.display = 'none';
            if(data.success) {
                document.getElementById('preview').style.display = 'block';
            }
        }

        async function handleFileUpload(file) {
            if(!file) return;
            document.getElementById('progressBarContainer').style.display = 'block';
            let fd = new FormData();
            fd.append('file', file);

            let xhr = new XMLHttpRequest();
            xhr.open('POST', '/upload_local', true);
            xhr.upload.onprogress = (e) => {
                if(e.lengthComputable) {
                    document.getElementById('progressBar').style.width = (e.loaded / e.total * 100) + '%';
                }
            };
            xhr.onload = function() {
                let res = JSON.parse(xhr.responseText);
                if(res.success) {
                    uploadedPath = res.path;
                    document.getElementById('progressBarContainer').style.display = 'none';
                    document.getElementById('preview').style.display = 'block';
                }
            };
            xhr.send(fd);
        }

        function startProcessing() {
            document.getElementById('preview').style.display = 'none';
            document.getElementById('viz').style.display = 'flex';
            
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/process_local';
            const params = {
                path: uploadedPath,
                url: document.getElementById('urlInput').value,
                format: document.getElementById('format').value,
                start: document.getElementById('startS').value || 0,
                end: document.getElementById('endS').value || ''
            };
            for(let key in params) {
                let i = document.createElement('input'); i.type='hidden'; i.name=key; i.value=params[key];
                form.appendChild(i);
            }
            document.body.appendChild(form); 
            form.submit();
            
            // Reset UI after a delay
            setTimeout(() => { document.getElementById('viz').style.display = 'none'; }, 5000);
        }
    </script>
</body>
</html>
'''

@app.route('/upload_local', methods=['POST'])
def upload_local():
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return jsonify({'success': True, 'path': path})

@app.route('/get')
def get_info():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'success': True, 'title': info.get('title')})
    except: return jsonify({'success': False})

@app.route('/process_local', methods=['POST'])
def process_local():
    path = request.form.get('path')
    url = request.form.get('url')
    fmt = request.form.get('format')
    start = float(request.form.get('start'))
    end = request.form.get('end')

    # If URL was provided, download it first
    if url and not path:
        ydl_opts = {'format': 'best', 'outtmpl': 'uploads/%(title)s.%(ext)s'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)

    clip = VideoFileClip(path)
    if end: clip = clip.subclip(start, float(end))
    else: clip = clip.subclip(start)

    output_name = "z_ether_" + str(int(time.time()))
    
    if fmt == 'gif':
        output_path = os.path.join(DOWNLOAD_FOLDER, output_name + ".gif")
        clip = clip.resize(width=480) # Auto-compression
        clip.write_gif(output_path, fps=10)
    elif fmt == 'mp3':
        output_path = os.path.join(DOWNLOAD_FOLDER, output_name + ".mp3")
        clip.audio.write_audiofile(output_path, bitrate="320k")
    else:
        output_path = os.path.join(DOWNLOAD_FOLDER, output_name + ".mp4")
        clip.write_videofile(output_path, codec="libx264", bitrate="1500k")

    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    

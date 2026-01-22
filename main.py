from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('downloads', exist_ok=True)

# Polished UI with Theme Support, File Upload, and Custom Modals
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Z LOADER PREMIUM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #ff3d00; 
            --primary-glow: rgba(255, 61, 0, 0.5);
            --bg: #0b0b0b; 
            --card: #161616; 
            --input: #1f1f1f; 
        }
        
        body.theme-blue { --primary: #0088ff; --primary-glow: rgba(0, 136, 255, 0.5); }
        body.theme-purple { --primary: #a020f0; --primary-glow: rgba(160, 32, 240, 0.5); }
        body.theme-orange { --primary: #ff3d00; --primary-glow: rgba(255, 61, 0, 0.5); }

        body { 
            font-family: 'Inter', sans-serif; background: var(--bg); color: white; 
            margin: 0; display: flex; justify-content: center; align-items: center; 
            min-height: 100vh; padding: 20px; box-sizing: border-box; overflow-x: hidden;
        }
        
        /* CUSTOM NOTIFICATION MODAL */
        #customAlert {
            position: fixed; top: -100px; left: 50%; transform: translateX(-50%);
            background: #222; border: 1px solid var(--primary); padding: 15px 25px;
            border-radius: 15px; z-index: 1000; transition: 0.5s cubic-bezier(0.18, 0.89, 0.32, 1.28);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 10px;
        }
        #customAlert.show { top: 25px; }

        .hamburger { position: fixed; top: 25px; right: 25px; z-index: 100; cursor: pointer; padding: 10px; }
        .hamburger div { width: 25px; height: 3px; background: white; margin: 5px; transition: 0.3s; border-radius: 5px; }

        .menu-overlay {
            position: fixed; top: 0; right: -100%; width: 260px; height: 100%;
            background: rgba(22, 22, 22, 0.98); backdrop-filter: blur(15px);
            z-index: 99; transition: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            padding: 80px 25px; border-left: 1px solid #333;
        }
        .menu-overlay.active { right: 0; }
        
        .card { 
            background: var(--card); padding: 35px; border-radius: 40px; 
            width: 100%; max-width: 420px; text-align: center;
            box-shadow: 0 40px 100px rgba(0,0,0,0.9); border: 1px solid #222;
            animation: slideIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        @keyframes slideIn { from { transform: translateY(60px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

        h2 { font-weight: 900; letter-spacing: -2px; margin-bottom: 25px; background: linear-gradient(45deg, var(--primary), #ffffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-transform: uppercase; }

        input[type="text"] { width: 100%; padding: 18px; margin-bottom: 15px; border-radius: 20px; border: 1px solid #333; background: var(--input); color: white; box-sizing: border-box; font-size: 15px; transition: 0.3s; }
        input:focus { border-color: var(--primary); outline: none; box-shadow: 0 0 20px var(--primary-glow); }

        .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .btn { padding: 16px; border-radius: 20px; border: none; font-weight: 700; cursor: pointer; transition: 0.3s; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
        .fetch-btn { background: #252525; color: #fff; border: 1px solid #333; }
        .find-btn { background: var(--primary); color: white; box-shadow: 0 10px 20px var(--primary-glow); }
        
        /* DOWNLOAD ANIMATION */
        .dl-progress-container { width: 100%; background: #222; height: 6px; border-radius: 10px; margin-top: 15px; overflow: hidden; display: none; }
        .dl-bar { width: 0%; height: 100%; background: var(--primary); transition: width 0.3s; box-shadow: 0 0 10px var(--primary-glow); }

        #preview { display: none; margin-top: 25px; animation: fadeIn 0.5s ease; }
        #thumbWrapper { width: 180px; height: 180px; margin: 0 auto 20px; background: #111; overflow: hidden; position: relative; box-shadow: 0 15px 40px rgba(0,0,0,0.5); }
        #thumb { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 0.6s; }
        .shape-music { border-radius: 50% !important; border: 5px solid var(--primary) !important; animation: spin 10s linear infinite; }
        .shape-video { border-radius: 25px !important; border: 1px solid #333 !important; }

        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .loader { display: none; margin: 20px auto; width: 30px; height: 30px; border: 3px solid #222; border-top-color: var(--primary); border-radius: 50%; animation: loadSpin 0.8s linear infinite; }
        @keyframes loadSpin { to { transform: rotate(360deg); } }
    </style>
</head>
<body class="theme-orange">

    <div id="customAlert"><span id="alertIcon">⚠️</span> <span id="alertText">Message</span></div>

    <div class="hamburger" onclick="toggleMenu()">
        <div></div><div></div><div></div>
    </div>

    <div class="menu-overlay" id="menu">
        <h3>APPEARANCE</h3>
        <div onclick="setTheme('orange')">Orange Fusion</div>
        <div onclick="setTheme('blue')">Electric Blue</div>
        <div onclick="setTheme('purple')">Deep Purple</div>
    </div>

    <div class="card">
        <h2>Z LOADER</h2>
        <input type="text" id="urlInput" placeholder="Paste link or use Find Music...">
        
        <div class="btn-grid">
            <button class="btn fetch-btn" onclick="getInfo()">Analyze</button>
            <button class="btn find-btn" onclick="openMusicMenu()">🎵 Find Music</button>
        </div>

        <input type="file" id="fileUpload" accept=".mp3,.aac,.wav,.m4a" style="display:none;" onchange="handleFileUpload()">

        <div id="loading" class="loader"></div>
        
        <div id="preview">
            <div id="thumbWrapper" class="shape-video"><img id="thumb" src=""></div>
            <p id="title" style="font-size: 14px; font-weight: 700; margin-bottom: 5px;"></p>
            <p id="extraDetails" style="font-size: 12px; color: #888; margin-bottom: 15px;"></p>
            
            <div class="dl-progress-container" id="progCont"><div class="dl-bar" id="progBar"></div></div>

            <select id="quality" style="width:100%; padding:15px; border-radius:15px; background:#1f1f1f; color:white; border:1px solid #333; margin-top:15px;">
                <option value="mp3">Audio (MP3 320kbps)</option>
                <optgroup id="videoList" label="Video Versions"></optgroup>
            </select>
            
            <button class="btn find-btn" style="width:100%; margin-top:15px;" id="dlBtn" onclick="startDownload()">Start Download</button>
        </div>
    </div>

    <script>
        function showAlert(msg, isError=true) {
            const alert = document.getElementById('customAlert');
            document.getElementById('alertText').innerText = msg;
            document.getElementById('alertIcon').innerText = isError ? '❌' : '✅';
            alert.classList.add('show');
            setTimeout(() => alert.classList.remove('show'), 3000);
        }

        function toggleMenu() { document.getElementById('menu').classList.toggle('active'); }
        function setTheme(theme) { document.body.className = 'theme-' + theme; localStorage.setItem('zTheme', theme); toggleMenu(); }

        function openMusicMenu() {
            const url = document.getElementById('urlInput').value;
            if(url) { identifyMusic(url); } 
            else { document.getElementById('fileUpload').click(); }
        }

        async function handleFileUpload() {
            const file = document.getElementById('fileUpload').files[0];
            if(!file) return;
            
            document.getElementById('loading').style.display = 'block';
            let formData = new FormData();
            formData.append('file', file);

            try {
                const res = await fetch('/upload_identify', { method: 'POST', body: formData });
                const data = await res.json();
                document.getElementById('loading').style.display = 'none';
                if(data.success) { showResults(data); } 
                else { showAlert("Could not find music data."); }
            } catch(e) { showAlert("Upload failed."); }
        }

        function showResults(data) {
            document.getElementById('preview').style.display = 'block';
            document.getElementById('title').innerText = data.track;
            document.getElementById('extraDetails').innerText = data.details;
            document.getElementById('thumb').src = data.thumb || 'https://via.placeholder.com/180';
            document.getElementById('thumb').onload = () => { document.getElementById('thumb').style.opacity = "1"; };
        }

        async function identifyMusic(url) {
            document.getElementById('loading').style.display = 'block';
            const res = await fetch('/identify?url=' + encodeURIComponent(url));
            const data = await res.json();
            document.getElementById('loading').style.display = 'none';
            if(data.success) { showResults(data); } 
            else { showAlert("No music data found."); }
        }

        function startDownload() {
            document.getElementById('progCont').style.display = 'block';
            let width = 0;
            const interval = setInterval(() => {
                if(width >= 90) clearInterval(interval);
                width += 5;
                document.getElementById('progBar').style.width = width + '%';
            }, 200);
            
            // Trigger actual form submission
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/download';
            const u = document.createElement('input'); u.type='hidden'; u.name='url'; u.value=document.getElementById('urlInput').value;
            const f = document.createElement('input'); f.type='hidden'; f.name='fid'; f.value=document.getElementById('quality').value;
            form.appendChild(u); form.appendChild(f);
            document.body.appendChild(form);
            form.submit();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload_identify', methods=['POST'])
def upload_identify():
    if 'file' not in request.files: return jsonify({'success': False})
    file = request.files['file']
    filename = secure_filename(file.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(path, download=False)
            # Use metadata if available, else filename
            track = info.get('track', filename)
            artist = info.get('artist', 'Local Upload')
            return jsonify({
                'success': True,
                'track': track,
                'details': f"Artist: {artist} | File: {filename}",
                'thumb': ''
            })
    except:
        return jsonify({'success': False})
    finally:
        if os.path.exists(path): os.remove(path)

# ... (Previous /identify, /get, and /download routes remain the same) ...

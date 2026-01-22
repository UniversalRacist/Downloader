from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import requests 

app = Flask(__name__)

# Full HTML with High-End Animations and Polished UI
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
        
        body { 
            font-family: 'Inter', sans-serif; background: var(--bg); color: white; 
            margin: 0; display: flex; justify-content: center; align-items: center; 
            min-height: 100vh; padding: 20px; box-sizing: border-box;
            overflow-x: hidden;
        }
        
        .card { 
            background: var(--card); padding: 35px; border-radius: 40px; 
            width: 100%; max-width: 420px; text-align: center;
            box-shadow: 0 40px 100px rgba(0,0,0,0.9); border: 1px solid #222;
            animation: slideIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
            backdrop-filter: blur(15px);
        }

        @keyframes slideIn { 
            from { transform: translateY(60px); opacity: 0; } 
            to { transform: translateY(0); opacity: 1; } 
        }

        h2 { 
            font-weight: 900; letter-spacing: -2px; margin-top: 0; margin-bottom: 25px;
            background: linear-gradient(45deg, #ff3d00, #ffae00);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-transform: uppercase;
        }

        input { 
            width: 100%; padding: 18px; margin-bottom: 15px; border-radius: 20px; 
            border: 1px solid #333; background: var(--input); color: white; 
            box-sizing: border-box; font-size: 15px; transition: 0.3s ease;
        }
        input:focus { border-color: var(--primary); outline: none; box-shadow: 0 0 20px var(--primary-glow); }

        .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 15px; }
        
        .btn { 
            padding: 16px; border-radius: 20px; border: none; 
            font-weight: 700; cursor: pointer; transition: 0.3s; 
            font-size: 13px; text-transform: uppercase;
        }
        .fetch-btn { background: #252525; color: #fff; border: 1px solid #333; }
        .shazam-btn { background: #0088ff; color: white; box-shadow: 0 10px 20px rgba(0, 136, 255, 0.3); }
        .direct-btn { background: rgba(255, 61, 0, 0.1); color: var(--primary); border: 1px solid var(--primary); grid-column: span 2; }
        
        .btn:active { transform: scale(0.95); }

        .dl-btn { 
            background: linear-gradient(135deg, #ff3d00 0%, #ff8e53 100%);
            color: white; display: none; margin-top: 20px; width: 100%;
            box-shadow: 0 15px 30px var(--primary-glow); font-size: 16px;
        }

        /* PREVIEW AREA */
        #preview { display: none; margin-top: 25px; animation: fadeIn 0.5s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }

        #thumbWrapper { 
            width: 200px; height: 200px; margin: 0 auto 20px; 
            background: #111; overflow: hidden; position: relative;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }
        #thumb { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.6s ease; }

        .shape-music { border-radius: 50% !important; border: 6px solid var(--primary) !important; animation: spin 8s linear infinite; }
        .shape-video { border-radius: 25px !important; border: 1px solid #333 !important; }

        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        select { 
            width: 100%; padding: 16px; border-radius: 18px; background: #1f1f1f !important; 
            color: white !important; border: 1px solid #333; appearance: none;
            background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='orange'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
            background-repeat: no-repeat; background-position: right 15px center;
        }

        .loader { 
            display: none; margin: 20px auto; width: 35px; height: 35px; 
            border: 4px solid #222; border-top-color: var(--primary); 
            border-radius: 50%; animation: loadSpin 0.8s linear infinite; 
        }
        @keyframes loadSpin { to { transform: rotate(360deg); } }

        #status { font-size: 11px; color: #555; margin-top: 25px; font-weight: 600; letter-spacing: 1.5px; }
        .secret { opacity: 0.05; font-size: 10px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>Z LOADER</h2>
        <input type="text" id="urlInput" placeholder="Paste link here...">
        
        <div class="btn-grid" id="mainActions">
            <button class="btn fetch-btn" onclick="getInfo()">Analyze</button>
            <button class="btn shazam-btn" onclick="identifyMusic()">🎵 Shazam</button>
            <button class="btn direct-btn" onclick="quickDownload()">Instant MP3 (320kbps)</button>
        </div>

        <div id="loading" class="loader"></div>
        
        <div id="preview">
            <div id="thumbWrapper" class="shape-video"><img id="thumb" src=""></div>
            <p id="title" style="font-size: 14px; font-weight: 700; margin-bottom: 5px;"></p>
            <p id="musicDetails" style="font-size: 12px; color: var(--primary); font-weight: 600; margin-bottom: 15px;"></p>
            
            <select id="quality" onchange="updateUI()">
                <option value="mp3">Audio (High Quality MP3)</option>
                <optgroup id="videoList" label="Video (MP4)"></optgroup>
            </select>
            
            <form id="dlForm" action="/download" method="post">
                <input type="hidden" name="url" id="hUrl">
                <input type="hidden" name="fid" id="hFid">
                <button type="submit" class="btn dl-btn" id="dlBtn">Download Now</button>
            </form>
        </div>
        <div id="status">ENCRYPTED CONNECTION</div>
        <div class="secret" onclick="handleSecret()">PRO CODE</div>
    </div>

    <script>
        function updateUI() {
            const q = document.getElementById('quality').value;
            const wrap = document.getElementById('thumbWrapper');
            wrap.className = (q === 'mp3') ? 'shape-music' : 'shape-video';
        }

        async function identifyMusic() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('status').innerText = "IDENTIFYING...";
            try {
                const res = await fetch('/identify?url=' + encodeURIComponent(url));
                const data = await res.json();
                document.getElementById('loading').style.display = 'none';
                if(data.success) {
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('musicDetails').innerText = "MATCH: " + data.label;
                    document.getElementById('status').innerText = "SONG IDENTIFIED";
                } else { alert("Could not find music data."); }
            } catch (e) { alert("API Error"); }
        }

        async function getInfo() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
            window.location.href = "app://show_ad"; 
            document.getElementById('loading').style.display = 'block';
            try {
                const res = await fetch('/get?url=' + encodeURIComponent(url));
                const data = await res.json();
                document.getElementById('loading').style.display = 'none';
                if(data.success) {
                    const img = document.getElementById('thumb');
                    img.src = data.thumb;
                    img.onload = () => { img.style.opacity = "1"; };
                    document.getElementById('title').innerText = data.title;
                    const vList = document.getElementById('videoList');
                    vList.innerHTML = '';
                    data.formats.forEach(f => {
                        const o = document.createElement('option');
                        o.value = f.id; o.innerText = f.res + ' HD Video';
                        vList.appendChild(o);
                    });
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('dlBtn').style.display = 'block';
                    document.getElementById('hUrl').value = url;
                    updateUI();
                }
            } catch (e) { alert("Server Error"); }
        }

        function quickDownload() {
            const url = document.getElementById('urlInput').value;
            if(!url) return alert("Paste link!");
            window.location.href = "app://show_ad";
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/download';
            const u = document.createElement('input'); u.type='hidden'; u.name='url'; u.value=url;
            const f = document.createElement('input'); f.type='hidden'; f.name='fid'; f.value='mp3';
            form.appendChild(u); form.appendChild(f);
            document.body.appendChild(form);
            form.submit();
        }

        function handleSecret() {
            let pass = prompt("Enter Code:");
            if(pass === "YouNigga") {
                window.location.href = "app://disable_ads";
                alert("Developer Mode Active");
            }
        }

        document.getElementById('dlForm').onsubmit = function() {
            document.getElementById('hFid').value = document.getElementById('quality').value;
            document.getElementById('dlBtn').innerText = "PROCESSING...";
            document.getElementById('dlBtn').disabled = true;
            window.location.href = "app://show_ad";
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/identify')
def identify():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            track = info.get('track')
            artist = info.get('artist')
            if track and artist:
                return jsonify({'success': True, 'label': f"{track} - {artist}"})
            return jsonify({'success': False})
    except:
        return jsonify({'success': False})

@app.route('/get')
def get():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen = set()
            for f in info.get('formats', []):
                height = f.get('height')
                if height and height not in seen and f.get('ext') == 'mp4':
                    formats.append({'id': f['format_id'], 'res': str(height) + 'p'})
                    seen.add(height)
            return jsonify({
                'success': True,
                'title': info.get('title'),
                'thumb': info.get('thumbnail'),
                'formats': sorted(formats, key=lambda x: int(x['res'].replace('p','')), reverse=True)[:5]
            })
    except:
        return jsonify({'success': False})

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    fid = request.form.get('fid')
    is_mp3 = fid == 'mp3'
    
    download_path = os.path.join(os.getcwd(), 'downloads')
    if not os.path.exists(download_path): os.makedirs(download_path)

    ydl_opts = {
        'format': 'bestaudio/best' if is_mp3 else f'{fid}+bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320',
        }] if is_mp3 else []
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if is_mp3: path = os.path.splitext(path)[0] + '.mp3'

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(path): os.remove(path)
            except: pass
            return response
        return send_file(path, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
                                    

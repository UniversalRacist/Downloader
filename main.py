from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Full HTML with Premium Animations, Fixed Thumbnails, and Dark UI Dropdowns
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Premium Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { 
            --primary: #ff3d00; 
            --primary-glow: rgba(255, 61, 0, 0.4);
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
            animation: slideUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
            backdrop-filter: blur(10px);
        }

        @keyframes slideUp { 
            from { transform: translateY(100px) scale(0.9); opacity: 0; } 
            to { transform: translateY(0) scale(1); opacity: 1; } 
        }

        h2 { 
            font-weight: 800; letter-spacing: -1.5px; margin-top: 0; margin-bottom: 25px;
            background: linear-gradient(45deg, #ff3d00, #ff8e53);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }

        input { 
            width: 100%; padding: 18px; margin-bottom: 15px; border-radius: 18px; 
            border: 1px solid #333; background: var(--input); color: white; 
            box-sizing: border-box; font-size: 15px; transition: 0.3s;
        }
        input:focus { border-color: var(--primary); outline: none; box-shadow: 0 0 15px rgba(255, 61, 0, 0.2); }

        .btn-group { display: flex; gap: 10px; margin-bottom: 10px; }
        
        .btn { 
            width: 100%; padding: 16px; border-radius: 18px; border: none; 
            font-weight: 600; cursor: pointer; transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
            font-size: 14px;
        }
        .fetch-btn { background: #222; color: #fff; border: 1px solid #333; }
        .fetch-btn:hover { background: #2a2a2a; transform: translateY(-2px); }
        
        .direct-btn { background: rgba(255, 61, 0, 0.1); color: var(--primary); border: 1px solid var(--primary); }
        .direct-btn:hover { background: var(--primary); color: white; }

        .dl-btn { 
            background: var(--primary); color: white; display: none; 
            margin-top: 15px; font-size: 16px; font-weight: 800;
            box-shadow: 0 10px 25px rgba(255, 61, 0, 0.3);
        }
        .dl-btn:active { transform: scale(0.95); }

        /* PREVIEW AREA */
        .preview-box { margin-top: 25px; display: none; animation: fadeIn 0.6s ease; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        #thumbWrapper { 
            width: 220px; height: 220px; margin: 0 auto 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.6); 
            transition: 0.8s cubic-bezier(0.5, 0, 0.5, 1);
            background: #111; overflow: hidden; border: 1px solid #333;
            position: relative;
        }
        #thumb { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.5s; }

        .shape-music { border-radius: 50% !important; border: 6px solid var(--primary) !important; animation: rotateDisc 10s linear infinite; }
        .shape-video { border-radius: 24px !important; border: 2px solid #333 !important; }

        @keyframes rotateDisc { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        /* POLISHED DROPDOWN */
        select { 
            width: 100%; padding: 18px; border-radius: 15px; background: #1f1f1f !important; 
            color: white !important; border: 1px solid #333; margin-bottom: 15px;
            appearance: none; cursor: pointer;
        }
        
        option { background: #161616; color: white; }

        /* LOADING SPINNER */
        .loader { 
            display: none; margin: 20px auto; width: 40px; height: 40px; 
            border: 4px solid #222; border-top-color: var(--primary); 
            border-radius: 50%; animation: spin 0.8s linear infinite; 
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        #status { font-size: 12px; color: #555; margin-top: 20px; text-transform: uppercase; letter-spacing: 1px; }
        .secret-link { color: #161616; font-size: 10px; text-decoration: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>LOADER PRO</h2>
        <input type="text" id="urlInput" placeholder="Paste link here...">
        
        <div class="btn-group" id="mainActions">
            <button class="btn fetch-btn" onclick="getInfo()">Analyze</button>
            <button class="btn direct-btn" onclick="quickDownload()">Quick MP3</button>
        </div>

        <div id="loading" class="loader"></div>
        
        <div id="preview" class="preview-box">
            <div id="thumbWrapper" class="shape-video"><img id="thumb" src=""></div>
            <p id="title" style="font-size: 14px; font-weight: 600; margin-bottom: 15px;"></p>
            
            <select id="quality" onchange="updateUI()">
                <option value="mp3">MP3 (320kbps Music)</option>
                <optgroup id="videoList" label="Video (MP4 High Quality)"></optgroup>
            </select>
            
            <form id="dlForm" action="/download" method="post">
                <input type="hidden" name="url" id="hUrl">
                <input type="hidden" name="fid" id="hFid">
                <button type="submit" class="btn dl-btn" id="dlBtn">Download Now</button>
            </form>
        </div>
        <div id="status">Secure & Private</div>
        <div class="secret-link" onclick="handleSecret()">Secret Code</div>
    </div>

    <script>
        function updateUI() {
            const q = document.getElementById('quality').value;
            const wrap = document.getElementById('thumbWrapper');
            wrap.className = (q === 'mp3') ? 'shape-music' : 'shape-video';
        }

        async function getInfo() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
            
            // Trigger Ad in Sketchware
            window.location.href = "app://show_ad";

            document.getElementById('mainActions').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('status').innerText = "Connecting...";

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
                        o.value = f.id; o.innerText = f.res + ' (High Quality)';
                        vList.appendChild(o);
                    });
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('dlBtn').style.display = 'block';
                    document.getElementById('hUrl').value = url;
                    document.getElementById('status').innerText = "Media Found";
                    updateUI();
                } else {
                    document.getElementById('mainActions').style.display = 'flex';
                    document.getElementById('status').innerText = "Error: Invalid Link";
                }
            } catch (e) {
                document.getElementById('mainActions').style.display = 'flex';
                document.getElementById('loading').style.display = 'none';
                alert("Connection Error");
            }
        }

        function quickDownload() {
            const url = document.getElementById('urlInput').value;
            if(!url) return alert("Paste link first!");
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
            let pass = prompt("Enter Secret Code:");
            if(pass === "YouNigga") {
                window.location.href = "app://disable_ads";
                alert("Ads Disabled!");
            }
        }

        document.getElementById('dlForm').onsubmit = function() {
            document.getElementById('hFid').value = document.getElementById('quality').value;
            document.getElementById('dlBtn').innerText = "Processing...";
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

@app.route('/get')
def get():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
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
                'title': info.get('title', 'Media File'),
                'thumb': info.get('thumbnail', ''),
                'formats': sorted(formats, key=lambda x: int(x['res'].replace('p','')), reverse=True)[:5]
            })
    except Exception:
        return jsonify({'success': False})

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    fid = request.form.get('fid')
    is_mp3 = fid == 'mp3'
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'bestaudio/best' if is_mp3 else f'{fid}+bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
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
    # Fix for Render: Use Dynamic Port
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

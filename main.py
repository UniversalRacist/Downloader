from flask import Flask, render_template_string, request, send_file, after_this_request, jsonify
import yt_dlp
import os
import requests # New import for API calls

app = Flask(__name__)

# Full HTML with Music Recognition Tool
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Premium Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #ff3d00; --bg: #0b0b0b; --card: #161616; --input: #1f1f1f; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: white; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; box-sizing: border-box; overflow-x: hidden; }
        .card { background: var(--card); padding: 35px; border-radius: 40px; width: 100%; max-width: 420px; text-align: center; box-shadow: 0 40px 100px rgba(0,0,0,0.9); border: 1px solid #222; }
        h2 { font-weight: 800; background: linear-gradient(45deg, #ff3d00, #ff8e53); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        input { width: 100%; padding: 18px; margin-bottom: 15px; border-radius: 18px; border: 1px solid #333; background: var(--input); color: white; box-sizing: border-box; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }
        .btn { width: 100%; padding: 16px; border-radius: 18px; border: none; font-weight: 600; cursor: pointer; transition: 0.4s; font-size: 13px; }
        .fetch-btn { background: #222; color: #fff; border: 1px solid #333; }
        .shazam-btn { background: #0088ff; color: white; grid-column: span 2; margin-top: 5px; } /* Shazam Blue */
        .direct-btn { background: rgba(255, 61, 0, 0.1); color: var(--primary); border: 1px solid var(--primary); }
        .dl-btn { background: var(--primary); color: white; display: none; margin-top: 15px; font-weight: 800; width: 100%; }
        #thumbWrapper { width: 200px; height: 200px; margin: 0 auto 20px; background: #111; overflow: hidden; position: relative; border: 1px solid #333; }
        #thumb { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 0.5s; }
        .shape-music { border-radius: 50% !important; border: 5px solid var(--primary) !important; }
        select { width: 100%; padding: 18px; border-radius: 15px; background: #1f1f1f; color: white; border: 1px solid #333; margin-bottom: 15px; appearance: none; }
        #status { font-size: 12px; color: #555; margin-top: 20px; text-transform: uppercase; }
        .loader { display: none; margin: 20px auto; width: 40px; height: 40px; border: 4px solid #222; border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="card">
        <h2>LOADER PRO</h2>
        <input type="text" id="urlInput" placeholder="Paste link here...">
        
        <div class="btn-group" id="mainActions">
            <button class="btn fetch-btn" onclick="getInfo()">Analyze</button>
            <button class="btn direct-btn" onclick="quickDownload()">Quick MP3</button>
            <button class="btn shazam-btn" onclick="identifyMusic()">🎵 Identify Music (Shazam)</button>
        </div>

        <div id="loading" class="loader"></div>
        
        <div id="preview" style="display:none; margin-top:20px;">
            <div id="thumbWrapper" class="shape-video"><img id="thumb" src=""></div>
            <p id="title" style="font-size: 14px; font-weight: 700;"></p>
            <p id="musicDetails" style="font-size: 12px; color: #ff3d00; margin-bottom: 15px;"></p>
            
            <select id="quality"><option value="mp3">MP3 (320kbps)</option><optgroup id="videoList" label="Video"></optgroup></select>
            <form action="/download" method="post">
                <input type="hidden" name="url" id="hUrl">
                <input type="hidden" name="fid" id="hFid">
                <button type="submit" class="btn dl-btn" id="dlBtn" onclick="document.getElementById('hFid').value=document.getElementById('quality').value">Download Now</button>
            </form>
        </div>
        <div id="status">Secure & Private</div>
    </div>

    <script>
        async function identifyMusic() {
            const url = document.getElementById('urlInput').value;
            if(!url) return alert("Paste a link first!");
            
            document.getElementById('status').innerText = "Identifying Music...";
            document.getElementById('loading').style.display = 'block';

            try {
                const res = await fetch('/identify?url=' + encodeURIComponent(url));
                const data = await res.json();
                document.getElementById('loading').style.display = 'none';
                
                if(data.success) {
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('musicDetails').innerText = "Song: " + data.label;
                    document.getElementById('status').innerText = "Match Found!";
                } else {
                    alert("Could not identify the song.");
                }
            } catch (e) { alert("API Error"); }
        }

        async function getInfo() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
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
                    document.getElementById('preview').style.display = 'block';
                    document.getElementById('dlBtn').style.display = 'block';
                    document.getElementById('hUrl').value = url;
                }
            } catch (e) { alert("Error"); }
        }

        function quickDownload() {
            const url = document.getElementById('urlInput').value;
            if(!url) return;
            const form = document.createElement('form');
            form.method = 'POST'; form.action = '/download';
            const u = document.createElement('input'); u.type='hidden'; u.name='url'; u.value=url;
            const f = document.createElement('input'); f.type='hidden'; f.name='fid'; f.value='mp3';
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

@app.route('/identify')
def identify():
    url = request.args.get('url')
    try:
        # We use yt-dlp to get the internal metadata of the video/audio
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            # Most modern links (YouTube/Spotify) have music tags
            track = info.get('track')
            artist = info.get('artist')
            
            if track and artist:
                return jsonify({'success': True, 'label': f"{track} by {artist}"})
            else:
                return jsonify({'success': False})
    except:
        return jsonify({'success': False})

@app.route('/get')
def get():
    url = request.args.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'success': True, 'title': info.get('title'), 'thumb': info.get('thumbnail')})
    except:
        return jsonify({'success': False})

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    fid = request.form.get('fid')
    is_mp3 = fid == 'mp3'
    if not os.path.exists('downloads'): os.makedirs('downloads')
    ydl_opts = {'format': 'bestaudio/best' if is_mp3 else 'bestvideo+bestaudio/best', 'outtmpl': 'downloads/%(title)s.%(ext)s'}
    if is_mp3:
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '320'}]
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = ydl.prepare_filename(info)
        if is_mp3: path = os.path.splitext(path)[0] + '.mp3'
    @after_this_request
    def cleanup(response):
        try: os.remove(path)
        except: pass
        return response
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    

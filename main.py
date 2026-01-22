from flask import Flask, render_template_string, request, send_file, redirect
import yt_dlp
import os
import tempfile

app = Flask(__name__)

# This is the HTML the user see inside your Sketchware WebView
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Media Downloader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; text-align: center; padding: 20px; background: #121212; color: white; }
        input { width: 80%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; }
        button { padding: 10px 20px; background: #008080; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .footer { margin-top: 20px; font-size: 12px; color: #888; }
    </style>
</head>
<body>
    <h2>Video/Audio Downloader</h2>
    <form action="/download" method="get">
        <input type="text" name="url" placeholder="Paste link here (YouTube, etc.)" required><br>
        <select name="format" style="padding:10px; border-radius:5px; margin-bottom:10px;">
            <option value="mp3">MP3 (Audio)</option>
            <option value="mp4">MP4 (Video)</option>
        </select><br>
        <button type="submit">Download Now</button>
    </form>
    <div class="footer">Powered by Gemini & yt-dlp</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download')
def download():
    video_url = request.args.get('url')
    download_format = request.args.get('format', 'mp3')
    
    if not video_url:
        return "Please provide a URL", 400

    # Temporary directory to store the file before sending to Android
    tmpdir = tempfile.gettempdir()
    
    ydl_opts = {
        'format': 'bestaudio/best' if download_format == 'mp3' else 'best',
        'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    if download_format == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            # If we converted to MP3, the filename extension needs to be updated
            if download_format == 'mp3':
                filename = os.path.splitext(filename)[0] + ".mp3"

            return send_file(filename, as_attachment=True)
            
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Important for Render/Replit: use environment PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
  

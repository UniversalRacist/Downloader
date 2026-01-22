# Step 1: Use a lightweight Python 3.10 image
FROM python:3.10-slim

# Step 2: Install ffmpeg (Essential for MP3/GIF/MP4 processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
        && rm -rf /var/lib/apt/lists/*

        # Step 3: Create a directory for your app
        WORKDIR /app

        # Step 4: Copy requirements and install them
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        # Step 5: Copy your main.py and folders
        COPY . .

        # Step 6: Create folders for storage and give permissions
        RUN mkdir -p /tmp/uploads /tmp/downloads && chmod 777 /tmp/uploads /tmp/downloads

        # Step 7: Expose the port (7860 for Hugging Face, 8080 for Koyeb/Render)
        EXPOSE 7860

        # Step 8: Start the web server
        CMD ["gunicorn", "-b", "0.0.0.0:7860", "main:app"]
        
from flask import Flask, request, jsonify, Response, send_from_directory
import yt_dlp
from ytmusicapi import YTMusic
import requests
import os

app = Flask(__name__, static_folder="static")
ymusic = YTMusic()

# --- Şarkı arama endpointi ---
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    results = ymusic.search(query, filter="songs")
    songs = []
    for r in results:
        if "videoId" in r:
            songs.append({
                "title": r["title"],
                "artist": r["artists"][0]["name"] if r.get("artists") else "Unknown",
                "videoId": r["videoId"]
            })
    return jsonify(songs)

# --- Ham link çekme ---
@app.route("/get_url/<video_id>")
def get_url(video_id):
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "cookies": "cookies.txt"  # Tarayıcı çerez dosyası
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=False)
        url = info["url"]
    return jsonify({"url": url})

# --- Proxy stream ---
@app.route("/stream/<video_id>")
def stream(video_id):
    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "cookies": "cookies.txt"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=False)
            url = info["url"]

        def generate():
            with requests.get(url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        yield chunk

        return Response(generate(), content_type="audio/webm")
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- index.html ---
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# --- Run server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

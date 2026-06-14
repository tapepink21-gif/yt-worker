from flask import Flask, request, send_file, jsonify
import requests
import io
import os

app = Flask(__name__)

PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.syncpundit.io",
    "https://api.piped.projectsegfau.lt",
    "https://pipedapi.in.projectsegfau.lt",
    "https://piped-api.garudalinux.org",
    "https://pipedapi.adminforge.de",
]

def extract_video_id(url):
    if "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtube.com/shorts/" in url:
        return url.split("shorts/")[1].split("?")[0]
    return None

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    vid_id = extract_video_id(url)
    if not vid_id:
        return jsonify({"error": "Could not extract video ID"}), 400

    # Intentar cada instancia de Piped
    for instance in PIPED_INSTANCES:
        try:
            print(f"[piped] probando {instance} para {vid_id}")
            api_url = f"{instance}/streams/{vid_id}"
            resp = requests.get(api_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            
            if resp.status_code != 200:
                print(f"[piped] {instance} status {resp.status_code}")
                continue

            data = resp.json()
            title = data.get("title", vid_id)
            artist = data.get("uploader", "YouTube")

            audio_streams = data.get("audioStreams", [])
            if not audio_streams:
                print(f"[piped] {instance} sin streams")
                continue

            audio_streams.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
            audio_url = audio_streams[0].get("url")

            if not audio_url:
                continue

            print(f"[piped] descargando audio desde {instance}")
            audio_resp = requests.get(audio_url, timeout=120, stream=True,
                headers={"User-Agent": "Mozilla/5.0"})

            if audio_resp.status_code != 200:
                print(f"[piped] error descargando: {audio_resp.status_code}")
                continue

            audio_data = audio_resp.content
            if len(audio_data) == 0:
                continue

            print(f"[piped] bytes: {len(audio_data)}")
            safe_name = f"{artist} - {title}.mp3".replace("/", "-").replace("\\", "-")

            return send_file(
                io.BytesIO(audio_data),
                mimetype="audio/mpeg",
                as_attachment=True,
                download_name=safe_name
            )

        except Exception as e:
            print(f"[piped] error con {instance}: {e}")
            continue

    return jsonify({"error": "No se pudo descargar de YouTube"}), 500

@app.route("/")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

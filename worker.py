from flask import Flask, request, send_file, jsonify
import yt_dlp
import tempfile
import os
import io

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "audio.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_path,
                "quiet": True,
                "no_warnings": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["web_creator", "android_creator"],
                    }
                },
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
                artist = info.get("uploader", "YouTube")

            # Buscar el archivo descargado
            for f in os.listdir(tmpdir):
                filepath = os.path.join(tmpdir, f)
                with open(filepath, "rb") as fh:
                    data = fh.read()

                return send_file(
                    io.BytesIO(data),
                    mimetype="audio/mpeg",
                    as_attachment=True,
                    download_name=f"{artist} - {title}.mp3"
                )

        return jsonify({"error": "No audio downloaded"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

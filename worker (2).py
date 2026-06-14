from flask import Flask, request, send_file, jsonify
import yt_dlp
import tempfile
import os
import io

app = Flask(__name__)

def get_cookies_file():
    """Escribe las cookies de variable de entorno a un archivo temporal."""
    cookies_content = os.environ.get("YOUTUBE_COOKIES", "")
    if not cookies_content:
        return None
    
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(cookies_content)
    tmp.close()
    return tmp.name

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    cookies_file = get_cookies_file()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "audio.%(ext)s")
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": output_path,
                "quiet": False,
                "no_warnings": False,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                }],
            }

            if cookies_file:
                ydl_opts["cookiefile"] = cookies_file
                print(f"[worker] usando cookies de YOUTUBE_COOKIES")
            else:
                print(f"[worker] sin cookies")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
                artist = info.get("uploader", "YouTube")

            for f in os.listdir(tmpdir):
                filepath = os.path.join(tmpdir, f)
                with open(filepath, "rb") as fh:
                    data = fh.read()

                safe_name = f"{artist} - {title}.mp3".replace("/", "-").replace("\\", "-")
                print(f"[worker] descargado: {len(data)} bytes")
                return send_file(
                    io.BytesIO(data),
                    mimetype="audio/mpeg",
                    as_attachment=True,
                    download_name=safe_name
                )

        return jsonify({"error": "No audio downloaded"}), 500

    except Exception as e:
        print(f"[worker] error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cookies_file and os.path.exists(cookies_file):
            os.unlink(cookies_file)

@app.route("/")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

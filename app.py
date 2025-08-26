import os
from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)

# Create uploads folder if not exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "photo" not in request.files:
        return "No file uploaded", 400

    photo = request.files["photo"]
    if photo.filename == "":
        return "No selected file", 400

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], photo.filename)
    photo.save(filepath)

    return redirect(f"/uploads/{photo.filename}")

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

if __name__ == "__main__":
    app.run(debug=True)

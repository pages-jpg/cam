from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import os

app = Flask(__name__)

uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400
    file = request.files["file"]
    new_file = UploadedFile(
        filename=file.filename,
        data=file.read(),
        mimetype=file.mimetype
    )
    db.session.add(new_file)
    db.session.commit()
    return {"message": f"{file.filename} uploaded successfully!"}

@app.route("/file/<int:file_id>")
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return send_file(BytesIO(file.data), mimetype=file.mimetype, download_name=file.filename)

@app.route("/gallery")
def gallery():
    files = UploadedFile.query.all()
    return render_template("gallery.html", files=files)

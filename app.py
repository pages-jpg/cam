import os
from flask import Flask, request, render_template_string, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO

app = Flask(__name__)

# Connect to PostgreSQL (DATABASE_URL must be set in Render Environment Variables)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model for storing files in database
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)   # binary file data
    mimetype = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Home
@app.route("/")
def index():
    return "✅ Backend is running. Go to /gallery to see uploaded photos."

# Upload route
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

# Serve individual file
@app.route("/file/<int:file_id>")
def get_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    return send_file(BytesIO(file.data), mimetype=file.mimetype, download_name=file.filename)

# Gallery page
@app.route("/gallery")
def gallery():
    files = UploadedFile.query.all()
    # Simple HTML gallery
    html = """
    <h1>Gallery</h1>
    {% for file in files %}
        <div style="margin:10px; display:inline-block;">
            <img src="/file/{{ file.id }}" alt="{{ file.filename }}" width="200"><br>
            <small>{{ file.filename }}</small>
        </div>
    {% endfor %}
    """
    return render_template_string(html, files=files)

import os
from flask import Flask, request, render_template, render_template_string, redirect, session, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
from functools import wraps

app = Flask(__name__)

# Secret key for session
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey123")

# Database setup (PostgreSQL)
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Model for storing files
class UploadedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    mimetype = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Passkey
PASSKEY = os.getenv("GALLERY_PASSKEY", "0310")  # Change here or via Render environment

# Decorator to protect gallery
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect("/gallery-login")
        return f(*args, **kwargs)
    return decorated_function

# Routes
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

# Gallery login page
@app.route("/gallery-login", methods=["GET", "POST"])
def gallery_login():
    if request.method == "POST":
        key = request.form.get("passkey")
        if key == PASSKEY:
            session["authenticated"] = True
            return redirect("/gallery")
        else:
            return render_template_string("""
                <h2>Incorrect passkey!</h2>
                <a href="/gallery-login">Try again</a>
            """)
    return render_template_string("""
        <h1>Enter Passkey to Access Gallery</h1>
        <form method="POST">
            <input type="password" name="passkey" placeholder="Passkey" required>
            <button type="submit">Enter</button>
        </form>
    """)

# Gallery page (requires login every time)
@app.route("/gallery")
@login_required
def gallery():
    files = UploadedFile.query.all()
    html = """
    <h1>Gallery</h1>
    <a href="/">&#8592; Back to Upload</a>
    {% for file in files %}
        <div style="margin:10px; display:inline-block;">
            <img src="/file/{{ file.id }}" alt="{{ file.filename }}" width="200"><br>
            <small>{{ file.filename }}</small>
            <form method="POST" action="/delete/{{ file.id }}" style="margin-top:5px;">
                <button type="submit">Delete</button>
            </form>
        </div>
    {% endfor %}
    """
    return render_template_string(html, files=files)

# Delete file route
@app.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    file = UploadedFile.query.get_or_404(file_id)
    db.session.delete(file)
    db.session.commit()
    return redirect("/gallery")

# Run app
if __name__ == "__main__":
    app.run(debug=True)

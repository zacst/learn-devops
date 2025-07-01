from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Use environment variables to configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///fallback.db")
db = SQLAlchemy(app)

# A simple model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)

@app.route('/')
def home():
    message = Message.query.first()
    return message.text if message else "No message in DB"

if __name__ == '__main__':
    db.create_all()
    if not Message.query.first():
        db.session.add(Message(text="Hello, Brow — from DB!"))
        db.session.commit()
    app.run(host='0.0.0.0', port=5000)

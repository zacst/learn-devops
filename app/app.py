from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import time
import sys

app = Flask(__name__)

# Use environment variables to configure the database connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///fallback.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# A simple model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)

def wait_for_db(max_retries=30):
    """Wait for database to be available with retries"""
    for i in range(max_retries):
        try:
            # Test database connection within application context
            with app.app_context():
                with db.engine.connect() as connection:
                    connection.execute(db.text('SELECT 1'))
            print(f"Database connected successfully on attempt {i+1}")
            return True
        except Exception as e:
            print(f"Database connection attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                time.sleep(2)
            else:
                print("Failed to connect to database after all retries")
                return False
    return False

@app.route('/')
def home():
    try:
        message = Message.query.first()
        return message.text if message else "No message in DB"
    except Exception as e:
        return f"Database error: {str(e)}"

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        with db.engine.connect() as connection:
            connection.execute(db.text('SELECT 1'))
        return {"status": "healthy", "database": "connected"}, 200
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 500

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Wait for database to be available
    if not wait_for_db():
        print("Exiting due to database connection failure")
        sys.exit(1)
    
    # Create tables within application context
    with app.app_context():
        try:
            db.create_all()
            if not Message.query.first():
                db.session.add(Message(text="Hello from Flask with PostgreSQL!"))
                db.session.commit()
                print("Database initialized with sample data")
        except Exception as e:
            print(f"Error initializing database: {e}")
            sys.exit(1)
    
    print("Flask app starting on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
Database initialization script
Run this to create the database tables
"""
from app import app, db
from models import DataFile

def init_db():
    """Initialize database and create tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database initialized successfully!")
        print(f"✓ Database file: {app.config['SQLALCHEMY_DATABASE_URI']}")

if __name__ == '__main__':
    init_db()


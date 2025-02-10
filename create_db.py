from app import app, db  # Import your Flask app and SQLAlchemy instance

# Push an application context
with app.app_context():
    db.create_all()  # Create all tables
    print("Database tables created successfully!")
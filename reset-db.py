from app import app, db
from sqlalchemy import text

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Remove migration data if it exists
    try:
        db.engine.execute(text("DROP TABLE IF EXISTS alembic_version"))
    except:
        pass
    
    # Create all tables
    db.create_all()
    
    print("Database has been reset.") 
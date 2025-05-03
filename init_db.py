from source.modules.database import engine
from source.modules.models import Base

def init_database():
    print("Initializing database...")
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_database()
import asyncio
import sys
from sqlalchemy.exc import OperationalError
from sqlalchemy.future import select # Přidáno pro select
from sqlalchemy.ext.asyncio import AsyncSession # Přidáno pro AsyncSession
import source.modules.models  
from source.modules.database import engine, Base, SessionLocal # Přidáno SessionLocal
from source.modules.auth import hash_password # Přidáno hash_password
from source.modules.models import User # Přidáno User

async def create_admin_user(db: AsyncSession):
    """Vytvoří výchozího administrátorského uživatele, pokud neexistuje."""
    admin_email = "admin@admin.admin"
    admin_password = "Pixma120+"

    # Zkontroluje, zda admin uživatel již existuje
    result = await db.execute(select(User).filter(User.email == admin_email))
    existing_admin = result.scalar_one_or_none()

    if not existing_admin:
        hashed_admin_password = hash_password(admin_password)
        admin_user = User(
            email=admin_email,
            hashed_password=hashed_admin_password,
            role="admin" # Nastavení role na admin
        )
        db.add(admin_user)
        await db.commit()
        print(f"✅ Admin user '{admin_email}' created successfully.")
    else:
        print(f"ℹ️ Admin user '{admin_email}' already exists.")

async def init_database():
    print("Initializing database…")
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            print("✅ Database initialized successfully")
            
            # Vytvoření admin uživatele po inicializaci tabulek
            async with SessionLocal() as db_session:
                await create_admin_user(db_session)
            
            return
        except OperationalError as e:
            wait = attempt
            print(f"⚠️  Attempt {attempt}/{max_retries} failed: {e!r}")
            print(f"   Retrying in {wait}s…")
            await asyncio.sleep(wait)
    print(f"❌ Could not initialize database after {max_retries} retries")
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database())
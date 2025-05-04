import asyncio
import sys
from sqlalchemy.exc import OperationalError
import source.modules.models  
from source.modules.database import engine, Base

async def init_database():
    print("Initializing database…")
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn))
            print("✅ Database initialized successfully")
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
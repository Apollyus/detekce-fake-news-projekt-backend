import asyncio
from sqlalchemy import select
from source.modules.database import engine
from source.modules.models import UserFeedback, TelemetryRecord, User

async def display_table_data(model_class, limit=20):
    """Zobrazí záznamy z dané tabulky"""
    async with engine.begin() as conn:
        result = await conn.execute(select(model_class).limit(limit))
        records = result.scalars().all()
        
        print(f"\n=== {model_class.__tablename__} ({len(records)} záznamů) ===")
        for record in records:
            filtered_dict = {k: v for k, v in record.__dict__.items() if not k.startswith('_')}
            print(f"ID: {filtered_dict.get('id')}")
            for key, value in filtered_dict.items():
                if key != 'id':
                    print(f"  {key}: {value}")
            print("-" * 50)

async def show_feedback_with_telemetry(limit=10):
    """Zobrazí zpětnou vazbu včetně souvisejících telemetrických dat"""
    async with engine.begin() as conn:
        query = select(UserFeedback, TelemetryRecord).join(
            TelemetryRecord, 
            UserFeedback.telemetry_record_id == TelemetryRecord.id
        ).limit(limit)
        
        result = await conn.execute(query)
        records = result.all()
        
        print(f"\n=== Zpětná vazba s telemetrií ({len(records)} záznamů) ===")
        for feedback, telemetry in records:
            print(f"Feedback ID: {feedback.id}")
            print(f"  Rating: {feedback.rating}")
            print(f"  Comment: {feedback.comment}")
            print(f"  Is Correct: {feedback.is_correct}")
            print(f"  Prompt: {telemetry.prompt}")
            print(f"  Request ID: {telemetry.request_id}")
            print("-" * 50)

async def main():
    print("Načítání databázových záznamů...")
    
    # Seznam modelů, které chcete zobrazit
    await display_table_data(User)
    await display_table_data(TelemetryRecord)
    await display_table_data(UserFeedback)
    
    # Zobrazení propojených dat
    await show_feedback_with_telemetry()

if __name__ == "__main__":
    asyncio.run(main())
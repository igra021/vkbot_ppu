# run_migration.py
import aiosqlite
import os

async def migrate():
    db_path = os.path.join("db", "database.db")
    async with aiosqlite.connect(db_path) as db:
        # Добавляем колонку, если её нет
        await db.execute("ALTER TABLE conversations ADD COLUMN analytics_json TEXT")
        await db.commit()
        print("✅ Миграция выполнена: добавлено поле analytics_json")

# Запустите один раз
import asyncio
asyncio.run(migrate())
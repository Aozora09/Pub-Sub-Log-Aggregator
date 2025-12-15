# aggregator/main.py
import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

import redis.asyncio as redis
from database import engine, Base, get_db, AsyncSessionLocal
from models import ProcessedEvent, Stats

# --- KONFIGURASI ---
BROKER_URL = os.getenv("BROKER_URL", "redis://broker:6379/0")
QUEUE_NAME = "event_queue"

# --- SKEMA DATA (VALIDASI) ---
class EventSchema(BaseModel):
    topic: str
    event_id: str
    timestamp: str
    source: str
    payload: dict

# --- EVENT CONSUMER (BACKGROUND WORKER) ---
async def process_event_atomically(db: AsyncSession, event_data: dict):
    """
    IMPLEMENTASI T8 & T9: TRANSAKSI & IDEMPOTENCY
    Mencoba insert event. Jika duplikat (conflict), abaikan.
    Jika sukses, update statistik. Semua dalam satu transaksi atomik.
    """
    try:
        # 1. Prepare Insert dengan ON CONFLICT DO NOTHING (Idempotent)
        stmt = pg_insert(ProcessedEvent).values(
            event_id=event_data['event_id'],
            topic=event_data['topic'],
            source=event_data['source'],
            payload=event_data['payload']
        ).on_conflict_do_nothing(
            constraint='uq_topic_event_id' # Sesuai nama di models.py
        )
        
        result = await db.execute(stmt)
        
        # Cek apakah baris baru berhasil ditambahkan?
        # rowcount == 1 berarti event baru (sukses).
        # rowcount == 0 berarti event duplikat (diabaikan).
        if result.rowcount > 0:
            # 2. Jika event baru, update statistik (Atomic Update)
            # Upsert Stats: Jika topic belum ada insert, jika ada update count + 1
            stats_stmt = pg_insert(Stats).values(
                topic=event_data['topic'],
                count=1
            ).on_conflict_do_update(
                index_elements=['topic'],
                set_={'count': Stats.count + 1}
            )
            await db.execute(stats_stmt)
            print(f"[PROCESSED] {event_data['topic']} - {event_data['event_id']}")
        else:
            print(f"[DUPLICATE DROPPED] {event_data['event_id']}")

        await db.commit() # Commit transaksi
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Transaction failed: {e}")

async def consume_messages():
    """Looping mengambil pesan dari Redis"""
    r = redis.from_url(BROKER_URL)
    print("Consumer started. Waiting for events...")
    
    while True:
        try:
            # BLPOP: Blocking pop, tunggu sampai ada data (efisien, bukan busy wait)
            # Mengembalikan tuple (queue_name, data)
            item = await r.blpop(QUEUE_NAME, timeout=5)
            
            if item:
                event_json = item[1]
                event_data = json.loads(event_json)
                
                # Buka sesi DB baru untuk setiap event
                async with AsyncSessionLocal() as session:
                    await process_event_atomically(session, event_data)
                    
        except Exception as e:
            print(f"Consumer Error: {e}")
            await asyncio.sleep(1) # Backoff sederhana jika Redis down

# --- LIFECYCLE (STARTUP) ---
@asynccontextmanager
async def lifecycle(app: FastAPI):
    # Buat tabel di database saat startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Jalankan Consumer di Background
    task = asyncio.create_task(consume_messages())
    yield
    # Shutdown logic (jika ada)

app = FastAPI(lifespan=lifecycle)

# --- API ENDPOINTS ---

@app.post("/publish")
async def publish_event(event: EventSchema):
    """
    Menerima event dari Publisher dan menaruhnya di Redis.
    Konsep: Decoupling (Publisher tidak akses DB langsung).
    """
    try:
        r = redis.from_url(BROKER_URL)
        await r.rpush(QUEUE_NAME, event.model_dump_json())
        return {"status": "queued", "event_id": event.event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events")
async def get_events(topic: str = None, db: AsyncSession = Depends(get_db)):
    query = select(ProcessedEvent)
    if topic:
        query = query.where(ProcessedEvent.topic == topic)
    result = await db.execute(query.limit(100))
    return result.scalars().all()

@app.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Stats))
    return result.scalars().all()
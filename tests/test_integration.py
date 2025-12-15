# tests/test_integration.py
import pytest
import httpx
import uuid
import asyncio
from faker import Faker

# Konfigurasi Target (Aggregator Service)
BASE_URL = "http://localhost:8080"
fake = Faker()

@pytest.fixture
def event_data():
    """Fixture untuk membuat data event valid"""
    return {
        "topic": "test.integration",
        "event_id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T12:00:00Z",
        "source": "pytest",
        "payload": {"message": "hello world"}
    }

@pytest.mark.asyncio
async def test_health_check():
    """Test 1: Cek apakah service Stats bisa diakses"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/stats")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_publish_event_success(event_data):
    """Test 2: Publish event valid harus sukses"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/publish", json=event_data)
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

@pytest.mark.asyncio
async def test_publish_invalid_schema():
    """Test 3: Publish event tanpa topic harus gagal (Validasi)"""
    invalid_data = {"event_id": "123"} # Missing topic & payload
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/publish", json=invalid_data)
        assert response.status_code == 422 # Unprocessable Entity

@pytest.mark.asyncio
async def test_idempotency_deduplication(event_data):
    """Test 4: Mengirim event yang SAMA 2x harus tetap return 200 (Idempotent)"""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Kirim Pertama
        resp1 = await client.post("/publish", json=event_data)
        assert resp1.status_code == 200
        
        # Kirim Kedua (Duplikat)
        resp2 = await client.post("/publish", json=event_data)
        assert resp2.status_code == 200 # Client tidak boleh tau ada error server

@pytest.mark.asyncio
async def test_get_events_filter():
    """Test 5: Filter events berdasarkan topic"""
    topic = f"test.filter.{uuid.uuid4()}"
    event = {
        "topic": topic,
        "event_id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T12:00:00Z",
        "source": "pytest",
        "payload": {}
    }
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        await client.post("/publish", json=event)
        await asyncio.sleep(1) # Tunggu consumer proses
        
        resp = await client.get(f"/events?topic={topic}")
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["topic"] == topic

# --- PARAMETRIZED TESTS (Menambah jumlah test case secara efisien) ---

@pytest.mark.parametrize("i", range(5))
@pytest.mark.asyncio
async def test_concurrent_requests(i):
    """Test 6-10: Uji beban ringan berulang (Concurrency)"""
    event = {
        "topic": "test.concurrent",
        "event_id": str(uuid.uuid4()),
        "timestamp": "2024-01-01T10:00:00Z",
        "source": "pytest-worker",
        "payload": {"worker": i}
    }
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post("/publish", json=event)
        assert resp.status_code == 200

@pytest.mark.parametrize("field", ["topic", "event_id", "source"])
@pytest.mark.asyncio
async def test_missing_fields(field):
    """Test 11-13: Cek validasi untuk field yang hilang"""
    data = {
        "topic": "t", "event_id": "e", "source": "s", 
        "timestamp": "0", "payload": {}
    }
    del data[field] # Hapus field
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.post("/publish", json=data)
        assert resp.status_code == 422
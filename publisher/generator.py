# publisher/generator.py
import time
import uuid
import json
import random
import os
import requests
from datetime import datetime, timezone
from faker import Faker

# Konfigurasi
TARGET_URL = os.getenv("TARGET_URL", "http://aggregator:8080/publish")
EVENT_COUNT = int(os.getenv("EVENT_COUNT", "1000")) # Jumlah event yg akan dikirim
DELAY = float(os.getenv("DELAY", "0.1")) # Delay antar request (detik)

fake = Faker()

# Daftar Topik sesuai T4 (Hierarki)
TOPICS = [
    "server.api.request",
    "server.api.error",
    "user.auth.login",
    "user.auth.logout",
    "payment.gateway.timeout"
]

def generate_event():
    """Membuat payload event log standar"""
    return {
        "topic": random.choice(TOPICS),
        "event_id": str(uuid.uuid4()), # UUID unik v4
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "publisher-service-01",
        "payload": {
            "user_id": fake.random_int(min=1, max=1000),
            "ip": fake.ipv4(),
            "message": fake.sentence(),
            "latency_ms": random.randint(10, 500)
        }
    }

def send_event(event, is_retry=False):
    """Mengirim event ke Aggregator via HTTP POST"""
    try:
        response = requests.post(TARGET_URL, json=event, timeout=5)
        status = "SUCCESS" if response.status_code == 200 else "FAILED"
        tag = "[DUPLICATE/RETRY]" if is_retry else "[NEW]"
        print(f"{tag} Sent {event['event_id']} | Topic: {event['topic']} | Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send {event['event_id']}: {e}")

def main():
    print(f"Starting Publisher... Target: {TARGET_URL}")
    # Tunggu sebentar agar Aggregator siap sepenuhnya
    time.sleep(5) 
    
    for i in range(EVENT_COUNT):
        # 1. Buat Event Baru
        event = generate_event()
        send_event(event)
        
        # 2. SIMULASI DUPLIKASI (Penting untuk T3 & T9)
        # 30% kemungkinan terjadi 'network glitch' sehingga pesan dikirim ulang
        if random.random() < 0.30: 
            time.sleep(0.05) # Jeda dikit
            print(f">>> Simulating Network Retry for {event['event_id']}")
            send_event(event, is_retry=True)
            
        time.sleep(DELAY)

    print("Publisher finished generating events.")

if __name__ == "__main__":
    main()
# Distributed Log Aggregator System (Idempotent Consumer Pattern)

**Nama:** Azhari Rambe  
**NIM:** 11221019  
**Mata Kuliah:** Sistem Paralel dan Terdistribusi

## 📖 Deskripsi Proyek
Sistem ini adalah Log Aggregator berbasis microservices yang mengimplementasikan pola **Publish-Subscribe**. Sistem dirancang untuk menangani pengiriman event bervolume tinggi, menjamin konsistensi data menggunakan **Idempotent Consumer**, dan mencegah race condition dengan transaksi atomik.

### Komponen Arsitektur
1.  **Publisher:** Mensimulasikan client yang mengirim log dan kegagalan jaringan (duplikasi pesan).
2.  **Broker (Redis):** Message broker untuk decoupling dan buffering.
3.  **Aggregator:** Consumer yang memproses pesan, melakukan deduplikasi, dan menyimpan statistik.
4.  **Storage (PostgreSQL):** Penyimpanan persisten untuk log dan metrik statistik.

---

## 🚀 Cara Menjalankan (Run Instructions)

### Prasyarat
- Docker & Docker Compose terinstall.

### Langkah Run
1.  Clone repository ini.
2.  Jalankan perintah berikut di terminal:
    ```bash
    docker-compose up --build
    ```
3.  Tunggu hingga semua service sehat (Healthy).
4.  Akses API Aggregator di: `http://localhost:8080`.

---

## 🧪 Cara Menjalankan Testing
Proyek ini dilengkapi dengan **Integration Tests** (menggunakan Pytest) yang mencakup 13 skenario pengujian (Validation, Deduplication, Concurrency).

1.  Pastikan sistem Docker sudah berjalan (`docker-compose up -d`).
2.  Matikan sementara publisher agar pengujian tidak terganggu traffic tinggi:
    ```bash
    docker stop service_publisher
    ```
3.  Siapkan environment Python (lokal):
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate      # Windows
    pip install -r tests/requirements.txt
    ```
4.  Jalankan test:
    ```bash
    pytest tests/test_integration.py -v
    ```

---

## 📡 API Endpoints

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `POST` | `/publish` | Menerima event log baru (JSON). |
| `GET` | `/stats` | Melihat statistik jumlah event per topik (Real-time). |
| `GET` | `/events` | Melihat data log mentah (mendukung filter `?topic=...`). |
| `GET` | `/health` | Cek status kesehatan layanan. |

---

## 🛠️ Keputusan Desain & Asumsi
1.  **Idempotency:** Menggunakan `UNIQUE CONSTRAINT (topic, event_id)` pada PostgreSQL dengan strategi `ON CONFLICT DO NOTHING` untuk menangani pesan duplikat dari Publisher.
2.  **Jaringan:** Semua komunikasi antar-service berjalan di jaringan internal Docker (`internal_net`) dan terisolasi dari akses publik langsung kecuali port API 8080.
3.  **Persistensi:** Data disimpan menggunakan Docker Named Volumes (`pg_data`) untuk mencegah kehilangan data saat container restart.

---

## 📺 Video Demo
Link Video Demo: [Tuliskan Link YouTube Anda Di Sini]
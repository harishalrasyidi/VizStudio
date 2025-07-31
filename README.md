# NL2SQL Service

Microservice untuk mengkonversi bahasa natural (Bahasa Indonesia) menjadi query SQL menggunakan Google Gemini dan LangChain.

## Teknologi yang Digunakan

- FastAPI
- LangChain
- Google Gemini
- PostgreSQL
- Python 3.8+

## Struktur Proyek

```
Service_AI/
├── app/                    # Direktori utama aplikasi
│   ├── api/               # Endpoint API dan router
│   ├── core/              # Konfigurasi inti dan pengaturan
│   ├── db/                # Koneksi database dan query
│   ├── models/            # Model Pydantic untuk validasi data
│   ├── services/          # Logika bisnis dan integrasi LangChain
│   └── utils/             # Fungsi utilitas dan helper
└── tests/                 # Unit tests dan integration tests
```

## Instalasi

1. Clone repositori ini
2. Buat virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
4. Salin `.env.example` ke `.env` dan sesuaikan konfigurasi
5. Jalankan aplikasi:
   ```bash
   uvicorn app.main:app --reload
   ```

## Penggunaan API

### Endpoint: `/nl2sql`

**Request:**
```json
{
    "prompt": "tampilkan total penjualan per kategori"
}
```

**Response:**
```json
{
    "sql_query": "SELECT category, SUM(sales) FROM sales_table GROUP BY category"
}
```

## Pengembangan

- Gunakan `black` untuk formatting kode
- Jalankan tests dengan `pytest`
- Ikuti panduan kontribusi di `CONTRIBUTING.md`

## Lisensi

[MIT License](LICENSE)
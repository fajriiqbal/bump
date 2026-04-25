# Sistem Management Keuangan Pondok Pesantren

Project Django modular untuk manajemen santri, tagihan, pembayaran, kas, laporan, backup, dan notifikasi WhatsApp.

## Stack
- Django
- Django Template
- Tailwind CSS
- SQLite untuk development
- PostgreSQL untuk production

## Struktur Inti
- `accounts` untuk autentikasi dan role
- `students` untuk data santri
  - ada fitur import santri dari CSV/XLSX dan export Excel
- `finance` untuk tagihan, pembayaran, kas masuk/keluar
- `notifications` untuk WhatsApp reminder
- `reports` untuk export laporan
- `backup` untuk backup dan restore
- `dashboard` untuk ringkasan data

## Instalasi
1. Buat virtual environment.
2. Install dependency:
```bash
pip install -r requirements.txt
```
3. Set environment:
```env
SECRET_KEY=change-me
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
```
4. Migrasi database:
```bash
py manage.py makemigrations
py manage.py migrate
```
5. Buat superuser:
```bash
py manage.py createsuperuser
```
6. Jalankan server:
```bash
py manage.py runserver
```

## Build Tailwind
```bash
npm install
cmd /c npm run build:css
```

## Konfigurasi WhatsApp Otomatis
Menu `WhatsApp` dipakai untuk mengatur gateway dan template pesan reminder.

### 1. Buat Gateway
Buka `WhatsApp -> Gateway -> Tambah Gateway`, lalu isi:
- `name`: nama provider, misalnya `Fonnte` atau `Wablas`
- `api_url`: endpoint API pengiriman pesan dari provider
- `api_key`: token atau API key dari provider
- `sender`: identitas pengirim, jika provider memakainya
- `active`: centang jika gateway ini ingin dipakai

### 2. Buat Template Pesan
Buka `WhatsApp -> Template -> Tambah Template`, lalu isi:
- `code`: kode template unik, misalnya `bill_reminder`
- `title`: judul template yang mudah dibaca
- `body`: isi pesan. Kamu bisa pakai placeholder Django template seperti:
  - `{{ nama_santri }}`
  - `{{ jenis_pembayaran }}`
  - `{{ periode }}`
  - `{{ nominal }}`
  - `{{ sisa_tagihan }}`
  - `{{ jatuh_tempo }}`

### 3. Alur Kirim
- Dari menu `WhatsApp`, klik `Kirim` pada santri yang masih punya tagihan
- Atau klik `Buka WA` jika ingin kirim manual lewat browser
- Semua pengiriman tercatat ke `MessageLog`

### 4. Payload yang Dipakai Kode Saat Ini
Fungsi `send_whatsapp()` mengirim payload JSON seperti ini:
```json
{
  "target": "6281234567890",
  "message": "pesan reminder",
  "countryCode": "62"
}
```
Header yang dikirim:
```http
Authorization: API_KEY_KAMU
```

Pastikan format ini cocok dengan provider WhatsApp yang kamu pakai. Kalau provider-mu punya format payload berbeda, bagian `notifications/services.py` perlu disesuaikan.

## Run Development Bareng di Windows
Kalau mau `runserver` dan `watch:css` jalan bersamaan, pakai satu perintah ini:
```bash
npm run dev
```

Script ini akan:
- menjalankan Tailwind watch di background
- menjalankan Django `runserver` di terminal yang sama
- otomatis mematikan proses Tailwind saat server dihentikan

## Catatan Production
- Gunakan PostgreSQL dengan `DATABASE_URL` atau konfigurasi `DB_*`
- Jalankan `collectstatic`
- Aktifkan Whitenoise di server
- Atur `DEBUG=0`
- Database development memakai `db_dev.sqlite3` agar tidak bentrok dengan file lama.

## cPanel Deployment
1. Upload project ke folder aplikasi, misalnya `~/pesantren-app`.
2. Buat virtual environment di cPanel > Setup Python App atau lewat terminal.
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Set environment:
```env
SECRET_KEY=isi-secret-yang-kuat
DEBUG=0
ALLOWED_HOSTS=domainkamu.com,www.domainkamu.com
DB_ENGINE=mysql
DB_NAME=nama_database
DB_USER=user_database
DB_PASSWORD=password_database
DB_HOST=localhost
DB_PORT=3306
DEFAULT_FROM_EMAIL=noreply@domainkamu.com
```
5. Kalau hosting memakai MySQL shared hosting, buat database dan user di cPanel lalu isi nilainya ke `.env`.
6. Jalankan migrasi:
```bash
python manage.py migrate
```
7. Jalankan collectstatic:
```bash
python manage.py collectstatic --noinput
```
8. Arahkan aplikasi ke `passenger_wsgi.py` sebagai entry point.
9. Pastikan folder `media/` dan `staticfiles/` writable.
10. Bila perlu, set domain utama atau subdomain ke folder aplikasi yang sama.

## Command Terminal
```bash
C:\Users\acer\AppData\Local\Python\bin\python.exe manage.py makemigrations
C:\Users\acer\AppData\Local\Python\bin\python.exe manage.py migrate
C:\Users\acer\AppData\Local\Python\bin\python.exe manage.py createsuperuser
C:\Users\acer\AppData\Local\Python\bin\python.exe manage.py runserver
```

## Catatan Windows
- Jika PowerShell memblokir `npm run`, pakai `cmd /c npm run build:css` atau `npm.cmd run build:css`.
- Kalau `npm run dev` gagal karena policy PowerShell, jalankan dari `cmd` atau pastikan PowerShell mengizinkan script lokal.
- Jika alias `py` tidak tersedia, pakai path Python penuh seperti contoh di atas.

## Next Step yang Disarankan
- Tambahkan template CRUD lengkap untuk `PaymentType`, `Bill`, `Payment`, `Income`, `Expense`, dan `CashAccount`
- Tambahkan command/cron untuk reminder WhatsApp otomatis
- Tambahkan export PDF/Excel/CSV penuh untuk semua laporan
- Tambahkan backup/restore database terintegrasi

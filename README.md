# QA Hub - Intertech

QA Task Manager ve Baba Script Manager birleştirilmiş entegre QA platformu.

---

## 🚀 Hızlı Kurulum (Mac - Quick Start)

### Gereksinimler
- Python 3.11+
- Node.js 18+
- VPN bağlantısı (Jira ve MSSQL erişimi için)

### 1. Projeyi İndir ve Aç
```bash
# Zip'i çıkar
unzip qa-hub.zip
cd qa-hub
```

### 2. Backend Kurulum
```bash
cd backend

# Virtual environment oluştur
python3 -m venv venv

# Aktive et
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Başlat
python server.py
# VEYA
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend Kurulum (Yeni Terminal)
```bash
cd frontend

# Bağımlılıkları yükle
npm install

# Başlat
npm start
```

### 4. Tarayıcıda Aç
```
http://localhost:3000
```

Giriş: Kullanıcı adı olarak `SERCANO` yazın.

---

## 🌐 Proxy Ayarları (ÖNEMLİ)

Bu uygulama şirket proxy'sini kullanır. Proxy ayarları `backend/jira_api_client.py` dosyasında:

```python
PROXY_HOST = "10.125.24.215"
PROXY_PORT = "8080"
```

Eğer proxy adresi değiştiyse bu değerleri güncelleyin.

---

## 🌟 Özellikler

### Görev Yönetimi
- ✅ Task oluşturma, düzenleme, silme
- ✅ Kanban board görünümü
- ✅ Proje bazlı organizasyon
- ✅ PDF rapor export

### Jira Araçları (VPN Gerekli)
- 🔗 **Bug Bağla**: Base cycle'dan bug'ları mevcut cycle'a bağla
- 📝 **Cycle Add**: Cycle'a yeni testler ekle
- 🔄 **API Rerun**: API testlerini tekrar çalıştır
- 📋 **Jira Generator**: JSON'dan test case oluştur

### Test Analizi (VPN Gerekli)
- 📊 **Test Analizi**: MSSQL'den test sonuçlarını analiz et
- 📈 **API Analizi**: Microservice endpoint coverage analizi

### Admin Panel
- 👥 Kullanıcı yönetimi
- 🔐 Rol atama
- 📜 Audit log görüntüleme

---

## 📁 Proje Yapısı

```
qa-hub/
├── setup.sh               # Kurulum scripti
├── run.sh                 # Başlatma scripti
├── README.md
│
├── backend/
│   ├── server.py              # Ana FastAPI server
│   ├── jira_api_client.py     # Jira REST API client
│   ├── mssql_client.py        # MSSQL bağlantı client
│   ├── requirements.txt       # Python bağımlılıkları
│   ├── requirements.internal.txt  # Opsiyonel bağımlılıklar
│   └── data/
│       ├── qa_tasks.db        # SQLite veritabanı
│       ├── projects.json      # QA projeleri
│       └── cycles.json        # Cycle'lar
│
└── frontend/
    ├── src/
    │   ├── pages/             # Sayfa bileşenleri
    │   ├── components/        # UI bileşenleri
    │   ├── context/           # React context'ler
    │   └── lib/               # Yardımcı fonksiyonlar
    ├── package.json
    └── .env
```

---

## 🔧 Konfigürasyon

### Frontend (.env)
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Jira API (backend/jira_api_client.py)
```python
JIRA_BASE_URL = "https://jira.intertech.com.tr"
JIRA_AUTH_TOKEN = "Basic <token>"
```

### MSSQL (backend/mssql_client.py)
```python
MSSQL_CONFIG = {
    "server": "WIPREDB31.intertech.com.tr",
    "database": "TEST_DATA_MANAGEMENT"
}
```

---

## 🔐 VPN Gereksinimleri

Aşağıdaki özellikler VPN bağlantısı gerektirir:
- Jira API işlemleri (Bug Bağla, Cycle Add, vb.)
- MSSQL sorguları (Test Analizi, API Analizi)

**VPN olmadan** bu özellikler **DEMO modunda** çalışır.

---

## 🛠️ Sorun Giderme

### "ModuleNotFoundError" hatası
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" hatası
Backend'in çalıştığından emin olun:
```bash
curl http://localhost:8001/api/health
```

### Frontend boş sayfa gösteriyor
`.env` dosyasını kontrol edin:
```bash
cat frontend/.env
# REACT_APP_BACKEND_URL=http://localhost:8001 olmalı
```

### Jira/MSSQL bağlanmıyor
VPN'e bağlı olduğunuzdan emin olun. VPN olmadan DEMO modu çalışır.

---

## 👤 Varsayılan Admin

Kullanıcı adı: `SERCANO` (otomatik admin yetkisi)

---

## 📞 Destek

Sorularınız için: sercan.onal@intertech.com.tr

---

## 📝 Lisans

Internal use only - Intertech

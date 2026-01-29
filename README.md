# QA Hub - Intertech

QA Task Manager ve Baba Script Manager birleştirilmiş entegre QA platformu.

## 🚀 Özellikler

### Görev Yönetimi
- Task oluşturma, düzenleme, silme
- Kanban board görünümü
- Proje bazlı organizasyon
- Kategori ve etiketleme
- PDF rapor export

### Jira Araçları
- **Bug Bağla**: Base cycle'dan bug'ları mevcut cycle'a bağla
- **Cycle Add**: Cycle'a yeni testler ekle
- **API Rerun**: API testlerini tekrar çalıştır
- **Jira Generator**: JSON'dan test case oluştur

### Test Analizi
- **Test Analizi**: MSSQL'den test sonuçlarını analiz et
- **API Analizi**: Microservice endpoint coverage analizi

### Admin Panel
- Kullanıcı yönetimi ve rol atama
- Audit log görüntüleme ve temizleme

---

## 🛠️ Localhost Kurulumu

### Gereksinimler
- Python 3.11+
- Node.js 18+
- VPN bağlantısı (Jira ve MSSQL erişimi için)

### 1. Repository'yi Klonla
```bash
git clone <repository-url>
cd qa-hub
```

### 2. Backend Kurulumu
```bash
cd backend

# Virtual environment oluştur
python -m venv venv

# Aktive et
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyası oluştur (opsiyonel)
cp .env.example .env
```

### 3. Frontend Kurulumu
```bash
cd frontend

# Bağımlılıkları yükle
npm install
# veya
yarn install

# .env dosyası oluştur
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env
```

### 4. Uygulamayı Başlat

#### Terminal 1 - Backend:
```bash
cd backend
source venv/bin/activate  # veya Windows'ta: venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Terminal 2 - Frontend:
```bash
cd frontend
npm start
# veya
yarn start
```

### 5. Tarayıcıda Aç
```
http://localhost:3000
```

---

## 📁 Proje Yapısı

```
qa-hub/
├── backend/
│   ├── server.py              # Ana FastAPI server
│   ├── jira_api_client.py     # Jira REST API client
│   ├── mssql_client.py        # MSSQL bağlantı client
│   ├── requirements.txt       # Python bağımlılıkları
│   └── data/
│       ├── qa_tasks.db        # SQLite veritabanı
│       ├── projects.json      # QA projeleri
│       └── cycles.json        # Cycle'lar
│
├── frontend/
│   ├── src/
│   │   ├── pages/             # Sayfa bileşenleri
│   │   ├── components/        # UI bileşenleri
│   │   ├── context/           # React context'ler
│   │   └── lib/               # Yardımcı fonksiyonlar
│   ├── package.json
│   └── .env
│
└── README.md
```

---

## 🔧 Konfigürasyon

### Jira API (backend/jira_api_client.py)
```python
JIRA_BASE_URL = "https://jira.intertech.com.tr"
JIRA_API_URL = f"{JIRA_BASE_URL}/rest/tests/1.0/"
JIRA_AUTH_TOKEN = "Basic <token>"
```

### MSSQL (backend/mssql_client.py)
```python
MSSQL_CONFIG = {
    "server": "WIPREDB31.intertech.com.tr",
    "user": "quantra",
    "password": "quantra2",
    "database": "TEST_DATA_MANAGEMENT"
}
```

---

## 🔐 VPN Gereksinimleri

Aşağıdaki özellikler VPN bağlantısı gerektirir:
- Jira API işlemleri (Bug Bağla, Cycle Add, vb.)
- MSSQL sorguları (Test Analizi, API Analizi)

VPN olmadan bu özellikler **DEMO modunda** çalışır ve mock data döndürür.

---

## 📋 API Endpoints

### Auth
- `POST /api/auth/register` - Kullanıcı girişi (sadece username)

### Tasks
- `GET /api/tasks` - Task listesi
- `POST /api/tasks` - Yeni task
- `PUT /api/tasks/{id}` - Task güncelle
- `DELETE /api/tasks/{id}` - Task sil

### Jira Tools
- `POST /api/jira-tools/bugbagla/analyze` - Bug bağlama analizi
- `POST /api/jira-tools/bugbagla/bind` - Bug bağla
- `POST /api/jira-tools/cycleadd/analyze` - Cycle ekleme analizi
- `POST /api/jira-tools/cycleadd/execute` - Cycle'a ekle

### Analysis
- `POST /api/analysis/analyze` - Test analizi
- `POST /api/analysis/apianaliz` - API analizi

### Admin
- `GET /api/audit-logs` - Audit logları
- `DELETE /api/audit-logs` - Logları temizle
- `POST /api/users/assign-role` - Rol atama

---

## 🎨 Teknolojiler

### Backend
- FastAPI (Python)
- SQLite (yerel veritabanı)
- MSSQL (uzak veritabanı - VPN)
- SSE (Server-Sent Events)

### Frontend
- React 18
- TailwindCSS
- Shadcn/UI
- Framer Motion

---

## 👤 Varsayılan Admin

Kullanıcı adı: `SERCANO` (otomatik admin yetkisi)

---

## 📞 Destek

Sorularınız için: sercan.onal@intertech.com.tr

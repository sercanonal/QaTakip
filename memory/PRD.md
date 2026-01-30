# QA Hub - Intertech

## Problem Statement
Kullanıcı, mevcut "QA Task Manager" uygulamasını, arkadaşına ait olan "Baba Script Manager" adlı uygulaması ile birleştirmek istedi. Bu yeni birleşik uygulamanın adı "QA Hub" olarak belirlendi.

## User Personas
- **QA Mühendisleri**: Test yönetimi, Jira entegrasyonu, test analizi
- **QA Yöneticileri**: Raporlama, proje takibi

## Core Requirements

### Birleştirilmiş Uygulama (QA Hub)
1. **QA Task Manager özellikleri:**
   - ✅ Görev yönetimi (CRUD)
   - ✅ Proje yönetimi
   - ✅ Kullanıcı yönetimi ve roller
   - ✅ Rapor export (PDF)
   - ✅ Dashboard ve istatistikler
   - ✅ Takvim entegrasyonu

2. **Baba Script Manager özellikleri:**
   - ✅ Jira Generator - JSON'dan test case oluşturma
   - ✅ Bug Bağla - Bug'ları test sonuçlarına bağlama (Backend port edildi)
   - ✅ Test Analizi - Cycle ve test durumu analizi (Backend port edildi)
   - ✅ Cycle Add - Cycle'a test ekleme (Backend port edildi)
   - ✅ API Analizi - API endpoint analizi (Backend port edildi)

3. **Dinamik Yönetim:**
   - ✅ QA Projeleri - Ayarlar sayfasından CRUD yönetimi
   - ✅ Team Remote ID desteği
   - ✅ Mobil proje işaretleme (iOS/Android platform seçimi)
   - ✅ Cycle'lar - Ayarlar sayfasından CRUD yönetimi
   - ✅ Projeler dinamik olarak Analiz ve Jira Araçları sayfalarına besleniyor

### UI/UX Gereksinimleri
- ✅ Modern koyu tema (dark mode)
- ✅ Sol tarafta sidebar navigasyon
- ✅ Mor/mavi/cyan gradient renkli tab'lar ve butonlar
- ✅ Glass-morphism kartlar
- ✅ Real-time SSE streaming output

### Teknik Gereksinimler
- ✅ FastAPI (Python) backend
- ✅ React frontend
- ✅ SQLite veritabanı
- ✅ JSON dosya tabanlı proje/cycle depolama
- ✅ SSE (Server-Sent Events) streaming
- ✅ Jira/Zephyr Scale API client (Python/requests) - VPN + Proxy gerekli
- ✅ MSSQL client (Python/pymssql) - VPN gerekli

---

## What's Been Implemented (2026-01-30)

### Tamamlanan Özellikler
1. ✅ Admin paneli sidebar'dan kaldırıldı
2. ✅ Görevler sayfasında Jira filtresi eklendi (açma/kapama butonu)
3. ✅ Jira API client'a PROXY desteği eklendi (`10.125.24.215:8080`)
4. ✅ Zephyr Scale API endpoint'i düzeltildi (`/rest/tests/1.0/`)
5. ✅ MSSQL timeout'ları artırıldı (60 saniye)
6. ✅ Frontend .env localhost için ayarlandı
7. ✅ README.md Mac kurulum adımları ile güncellendi

### Proxy Ayarları (Kritik!)
Şirket ağında Jira'ya erişmek için proxy gerekli:
- **Proxy Host:** `10.125.24.215`
- **Proxy Port:** `8080`
- **Dosya:** `backend/jira_api_client.py`

---

## Prioritized Backlog

### P0 - Kritik (Kullanıcı tarafından test edilmeli)
- [ ] Jira task'larının backlog'da görünmesi (proxy ile)
- [ ] Test Analizi fonksiyonunun çalışması
- [ ] API Analizi fonksiyonunun çalışması

### P1 - Önemli
- [ ] Jira/MSSQL işlevselliğinin tam doğrulaması
- [ ] Bug Bağla fonksiyonunun testi
- [ ] Cycle Add fonksiyonunun testi

### P2 - İyileştirmeler
- [ ] Platform ikonları (iOS/Android görsel ayrımı)
- [ ] UI animasyonları (framer-motion)
- [ ] server.py refactoring (routes klasörüne ayrıştırma)

---

## Kurulum Notları

### Localhost Kurulum (Mac)
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py

# Frontend (yeni terminal)
cd frontend
npm install
npm start
```

### Giriş
Kullanıcı adı: `SERCANO` (admin yetkili)

---

## Dosya Referansları
- `/app/backend/jira_api_client.py` - Jira/Zephyr API client (PROXY destekli)
- `/app/backend/mssql_client.py` - MSSQL client
- `/app/backend/server.py` - Ana FastAPI server
- `/app/frontend/src/pages/Tasks.jsx` - Görevler sayfası (Jira filtresi)
- `/app/frontend/src/pages/Analysis.jsx` - Analiz sayfası
- `/app/README.md` - Kurulum talimatları

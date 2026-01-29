# QA Hub - Intertech

## Problem Statement
Kullanıcı, mevcut "QA Task Manager" uygulamasını, arkadaşına ait olan "Baba Script Manager" adlı uygulaması ile birleştirmek istedi. Bu yeni birleşik uygulamanın adı "QA Hub" olarak belirlendi.

## User Personas
- **QA Mühendisleri**: Test yönetimi, Jira entegrasyonu, test analizi
- **QA Yöneticileri**: Raporlama, proje takibi, admin paneli

## Core Requirements

### Birleştirilmiş Uygulama (QA Hub)
1. **QA Task Manager özellikleri:**
   - ✅ Görev yönetimi (CRUD)
   - ✅ Proje yönetimi
   - ✅ Kullanıcı yönetimi ve roller
   - ✅ Rapor export (PDF)
   - ✅ Admin paneli
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
- ✅ Framer Motion animasyonları
- ✅ Real-time SSE streaming output

### Teknik Gereksinimler
- ✅ FastAPI (Python) backend
- ✅ React frontend
- ✅ SQLite veritabanı
- ✅ JSON dosya tabanlı proje/cycle depolama
- ✅ SSE (Server-Sent Events) streaming
- ✅ Jira API client (Python/httpx) - VPN gerekli
- ✅ MSSQL client (Python/pymssql) - VPN gerekli

## What's Been Implemented

### Session 1 (29 Ocak 2025)
- ✅ QA Task Manager uygulaması oluşturuldu
- ✅ Görev, proje, kullanıcı yönetimi
- ✅ Admin paneli
- ✅ Rapor export

### Session 2 (29 Ocak 2025 - Birleştirme)
- ✅ Uygulama adı "QA Hub" olarak değiştirildi
- ✅ **Jira Araçları** sayfası eklendi (4 tab)
- ✅ **Analiz** sayfası eklendi (2 tab)
- ✅ Backend SSE streaming endpoint'leri
- ✅ Framer Motion animasyonları
- ✅ Modern gradient UI tasarımı (mor/mavi/cyan)

### Session 3 (30 Ocak 2025 - Dinamik Yönetim & JS Port)
- ✅ QA Projeleri CRUD API'leri (`/api/qa-projects`)
- ✅ **YENİ ALANLAR:** teamRemoteId, isMobile, platform (iOS/Android)
- ✅ Proje ekleme/düzenleme formları güncellendi
- ✅ Mobil proje için radio button seçimi (iOS/Android)
- ✅ **JavaScript'ten Python'a Port:**
  - `jira_api_client.py` - Jira REST API client (httpx)
  - `mssql_client.py` - MSSQL bağlantı client (pymssql)
  - Bug Bağla analyze/execute endpoint'leri
  - Cycle Add analyze/execute endpoint'leri
  - Test Analizi endpoint'i
  - API Analizi endpoint'i
- ✅ Settings sayfasında gelişmiş proje yönetimi UI

## Known Limitations
- **VPN Gerekli**: Jira API ve MSSQL bağlantıları VPN arkasından çalışacak
- **Demo Mode**: VPN olmadığında mock data döndürülüyor

## Technical Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Ana server dosyası
- `/app/backend/jira_api_client.py` - Jira API client (YENİ)
- `/app/backend/mssql_client.py` - MSSQL client (YENİ)
- `/app/backend/data/projects.json` - QA projeleri
- `/app/backend/data/cycles.json` - Cycle'lar
- `/app/backend/data/qa_tasks.db` - SQLite veritabanı

### Frontend (React)
- `/app/frontend/src/pages/Settings.jsx` - Proje/Cycle yönetimi (Güncellendi)
- `/app/frontend/src/pages/JiraTools.jsx` - Jira araçları (4 tab)
- `/app/frontend/src/pages/Analysis.jsx` - Test analizi (2 tab)

### API Endpoints
**Proje Yönetimi:**
- `GET/POST/PUT/DELETE /api/qa-projects`
- Yeni alanlar: teamRemoteId, isMobile, platform

**Jira Araçları:**
- `POST /api/jira-tools/bugbagla/analyze` - Bug bağlama analizi
- `POST /api/jira-tools/bugbagla/bind` - Bug bağlama
- `POST /api/jira-tools/cycleadd/analyze` - Cycle ekleme analizi
- `POST /api/jira-tools/cycleadd/execute` - Cycle ekleme

**Analiz:**
- `POST /api/analysis/analyze` - Test analizi
- `POST /api/analysis/apianaliz` - API analizi

## Prioritized Backlog

### P0 - Critical (TAMAMLANDI)
- [x] Dinamik proje yönetimi (Ayarlar'dan)
- [x] Team Remote ID desteği
- [x] Mobil proje işaretleme (iOS/Android)
- [x] JavaScript mantığının Python'a port edilmesi

### P1 - High Priority
- [ ] VPN ile gerçek Jira API testleri
- [ ] VPN ile gerçek MSSQL testleri

### P2 - Medium Priority
- [ ] LocalStorage form değerlerini hatırlama
- [ ] Export to CSV/Excel
- [ ] Gelişmiş filtreleme

### P3 - Low Priority
- [ ] Proje yönetimi (Sonar, Jenkins linkleri)
- [ ] Dark/Light tema toggle
- [ ] Daha fazla animasyon

## Test Reports
- `/app/test_reports/iteration_6.json` - Proje/Cycle CRUD testleri

## Jira API Configuration
```
Base URL: https://jira.intertech.com.tr/rest/tests/1.0/
Auth: Basic Auth (integration_user)
```

## MSSQL Configuration
```
Server: WIPREDB31.intertech.com.tr
Database: TEST_DATA_MANAGEMENT
User: quantra
```

## Next Steps
1. VPN ile gerçek Jira/MSSQL entegrasyonu test edilecek
2. Kullanıcı onayı sonrası production'a hazırlık

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

2. **Baba Script Manager özellikleri (Entegre Edildi):**
   - ✅ Jira Generator - JSON'dan test case oluşturma
   - ✅ Bug Bağla - Bug'ları test sonuçlarına bağlama
   - ✅ Test Analizi - Cycle ve test durumu analizi
   - ⏳ Cycle Add - Cycle'a test ekleme (placeholder)
   - ⏳ API Rerun - API testlerini tekrar çalıştırma (placeholder)

### UI/UX Gereksinimleri
- ✅ Modern koyu tema (dark mode)
- ✅ Sol tarafta sidebar navigasyon
- ✅ Gradient renkli tab'lar ve butonlar
- ✅ Glass-morphism kartlar
- ✅ Framer Motion animasyonları
- ✅ Real-time SSE streaming output

### Teknik Gereksinimler
- ✅ FastAPI (Python) backend
- ✅ React frontend
- ✅ SQLite veritabanı
- ✅ SSE (Server-Sent Events) streaming
- ⏳ Jira API entegrasyonu (VPN arkasından)
- ⏳ MSSQL entegrasyonu (VPN arkasından)

## What's Been Implemented

### Session 1 (29 Ocak 2025)
- ✅ QA Task Manager uygulaması oluşturuldu
- ✅ Görev, proje, kullanıcı yönetimi
- ✅ Admin paneli
- ✅ Rapor export

### Session 2 (29 Ocak 2025 - Birleştirme)
- ✅ Uygulama adı "QA Hub" olarak değiştirildi
- ✅ **Jira Araçları** sayfası eklendi:
  - Jira Generator tab
  - Bug Bağla tab
  - Cycle Add tab (placeholder)
  - API Rerun tab (placeholder)
- ✅ **Analiz** sayfası eklendi:
  - Test Analizi tab
  - API Analizi tab (placeholder)
- ✅ Backend SSE streaming endpoint'leri:
  - /api/jira-tools/jiragen/validate
  - /api/jira-tools/jiragen/create
  - /api/jira-tools/bugbagla/analyze
  - /api/jira-tools/bugbagla/bind
  - /api/analysis/analyze
  - /api/analysis/projects
- ✅ Framer Motion animasyonları
- ✅ Modern gradient UI tasarımı

## Known Limitations
- **VPN Gerekli**: Jira API ve MSSQL bağlantıları VPN arkasından çalışacak
- **Demo Mode**: VPN olmadığında mock data döndürülüyor
- **Localhost Export**: Tam fonksiyonellik için localhost'ta çalıştırma gerekli

## Technical Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Ana server dosyası
- `/app/backend/database.py` - SQLite bağlantısı
- SSE streaming ile real-time log

### Frontend (React)
- `/app/frontend/src/pages/JiraTools.jsx` - Jira araçları
- `/app/frontend/src/pages/Analysis.jsx` - Test analizi
- `/app/frontend/src/components/Layout.jsx` - Ana layout

### Data Sources
- SQLite: Kullanıcılar, görevler, projeler
- JSON dosyaları: Cycle'lar, konfigürasyon (ileride)
- MSSQL: Test verileri (VPN ile)

## Prioritized Backlog

### P0 - Critical
- [ ] Jira API gerçek entegrasyonu (localhost için)
- [ ] MSSQL bağlantısı (localhost için)

### P1 - High Priority
- [ ] Cycle Add implementasyonu
- [ ] API Rerun implementasyonu
- [ ] iOS/Android platform ayrımı (cycle adından)

### P2 - Medium Priority
- [ ] LocalStorage form değerlerini hatırlama
- [ ] Export to CSV/Excel
- [ ] Gelişmiş filtreleme

### P3 - Low Priority
- [ ] Proje yönetimi (Sonar, Jenkins linkleri)
- [ ] Dark/Light tema toggle
- [ ] Daha fazla animasyon

## Next Steps
1. Kullanıcı test edecek
2. VPN ile gerçek Jira/MSSQL entegrasyonu
3. Localhost export paketi hazırlama

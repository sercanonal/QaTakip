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
   - ✅ Jira Generator - JSON'dan test case oluşturma (UI hazır, VPN gerekli)
   - ✅ Bug Bağla - Bug'ları test sonuçlarına bağlama (UI hazır, VPN gerekli)
   - ✅ Test Analizi - Cycle ve test durumu analizi (UI hazır, VPN gerekli)
   - ✅ Cycle Add - Cycle'a test ekleme (UI hazır, VPN gerekli)
   - ✅ API Rerun - API testlerini tekrar çalıştırma (UI hazır, VPN gerekli)

3. **Dinamik Yönetim:**
   - ✅ QA Projeleri - Ayarlar sayfasından CRUD yönetimi
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
- ⏳ Jira API entegrasyonu (VPN arkasından, backend hazır)
- ⏳ MSSQL entegrasyonu (VPN arkasından)

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

### Session 3 (30 Ocak 2025 - Dinamik Yönetim)
- ✅ QA Projeleri CRUD API'leri (`/api/qa-projects`)
- ✅ Cycle'lar CRUD API'leri (`/api/cycles`)
- ✅ Settings sayfasında QA Projeleri yönetimi (tablo, ekleme, düzenleme, silme)
- ✅ Settings sayfasında Cycle'lar yönetimi (tablo, ekleme, silme)
- ✅ Analysis sayfası projeleri dinamik olarak API'den çekiyor
- ✅ Jira Tools sayfası projeleri dinamik olarak API'den çekiyor
- ✅ Test kapsamı: 15 backend testi, tüm frontend özellikleri doğrulandı

## Known Limitations
- **VPN Gerekli**: Jira API ve MSSQL bağlantıları VPN arkasından çalışacak
- **Demo Mode**: VPN olmadığında mock data döndürülüyor
- **Localhost Export**: Tam fonksiyonellik için localhost'ta çalıştırma gerekli

## Technical Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Ana server dosyası (~2600 satır)
- `/app/backend/data/projects.json` - QA projeleri
- `/app/backend/data/cycles.json` - Cycle'lar
- `/app/backend/data/qa_tasks.db` - SQLite veritabanı

### Frontend (React)
- `/app/frontend/src/pages/Settings.jsx` - Proje/Cycle yönetimi
- `/app/frontend/src/pages/JiraTools.jsx` - Jira araçları (4 tab)
- `/app/frontend/src/pages/Analysis.jsx` - Test analizi (2 tab)
- `/app/frontend/src/components/Layout.jsx` - Ana layout ve sidebar

### API Endpoints (Yeni)
- `GET/POST/PUT/DELETE /api/qa-projects` - QA Proje yönetimi
- `GET/POST/PUT/DELETE /api/cycles` - Cycle yönetimi

## Prioritized Backlog

### P0 - Critical (TAMAMLANDI)
- [x] Dinamik proje yönetimi (Ayarlar'dan)
- [x] Dinamik cycle yönetimi (Ayarlar'dan)
- [x] Analiz ve Jira Araçları sayfalarına dinamik proje besleme

### P1 - High Priority
- [ ] Jira API gerçek entegrasyonu (VPN ile test gerekli)
- [ ] MSSQL bağlantısı (VPN ile test gerekli)
- [ ] Orijinal JS script mantığının Python'a port edilmesi (dosyalar gerekli)

### P2 - Medium Priority
- [ ] iOS/Android platform ayrımı (cycle adından)
- [ ] LocalStorage form değerlerini hatırlama
- [ ] Export to CSV/Excel
- [ ] Gelişmiş filtreleme

### P3 - Low Priority
- [ ] Proje yönetimi (Sonar, Jenkins linkleri)
- [ ] Dark/Light tema toggle
- [ ] Daha fazla animasyon

## Test Reports
- `/app/test_reports/iteration_6.json` - Son test raporu (15/15 başarılı)
- `/app/backend/tests/test_qa_projects_cycles.py` - Backend unit testleri

## Next Steps
1. Kullanıcı test edecek
2. VPN ile gerçek Jira/MSSQL entegrasyonu
3. Orijinal JavaScript dosyalarından mantık port edilecek (dosyalar sağlanırsa)
4. Localhost export paketi hazırlama

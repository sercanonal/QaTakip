# QA Task Manager - Intertech

## Problem Statement
Intertech şirketinde QA mühendisleri için profesyonel iş takip uygulaması. Yoğun dönemlerde işlerin unutulmasını, karıştırılmasını veya tekrar yapılmasını önlemek için tasarlanmıştır.

## User Personas
- **Birincil**: QA Mühendisleri (API testi, UI testi, regresyon testleri)
- **İkincil**: Tüm Intertech çalışanları

## Core Requirements
- Cihaz tabanlı kimlik doğrulama (şifresiz, device_id + localStorage)
- Görev yönetimi (CRUD, durum, öncelik, kategori)
- Kanban board ile sürükle-bırak görev yönetimi
- Proje bazlı gruplandırma
- Takvim görünümü + Daily Standup özeti
- İlerleme raporları ve dashboard
- Akıllı Bugün Görünümü (Smart Today View)
- Bildirim sistemi
- Özelleştirilebilir kategoriler
- Türkçe arayüz

## Architecture
- **Backend**: FastAPI + SQLite (aiosqlite)
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Auth**: Cihaz tabanlı (device_id UUID, localStorage)
- **Database**: SQLite (dosya tabanlı, /app/backend/data/qa_tasks.db)

## What's Implemented (22 Ocak 2025)

### Core Features
- [x] Cihaz tabanlı kayıt/giriş sistemi (şifresiz)
- [x] Dashboard (istatistikler, son görevler, akıllı bugün görünümü)
- [x] Görev yönetimi (oluştur, düzenle, sil, durum değiştir)
- [x] Kanban board (4 sütun: Yapılacak, Devam Ediyor, Bloke, Tamamlandı)
- [x] Sürükle-bırak ile görev durumu değiştirme
- [x] Proje yönetimi (oluştur, düzenle, sil)
- [x] Takvim görünümü (tarih bazlı görevler)
- [x] Daily Standup Özeti (Dün tamamladım, Bugün devam edeceğim, vb.)
- [x] Raporlar sayfası (grafikler, istatistikler)
- [x] Ayarlar (kategori yönetimi)
- [x] Responsive sidebar navigasyon
- [x] Dark mode tasarım
- [x] Bildirim sistemi (in-app)

### Bug Fixes (22 Ocak 2025)
- [x] Oturum sorunu düzeltildi (localStorage'dan hemen kullanıcı yükleme)
- [x] Bildirim dropdown'u düzeltildi
- [x] Daily Summary endpoint ve UI eklendi
- [x] Görev silme sorunu düzeltildi (event propagation)
- [x] Clipboard API hatası için fallback eklendi
- [x] Takvimde seçili güne göre Daily Summary gösterimi eklendi
- [x] Kanban board 5 kolona genişletildi (Backlog, Bugün Başlamayı Planlıyorum, Devam Ediyor, Bloke, Tamamlandı)
- [x] Daily Summary popup eklendi (büyük dialog ile detaylı görünüm)

## API Endpoints
- `POST /api/auth/register` - Yeni kullanıcı kaydı
- `GET /api/auth/check/{device_id}` - Cihaz kontrolü
- `GET /api/tasks` - Görevleri listele
- `POST /api/tasks` - Görev oluştur
- `PUT /api/tasks/{id}` - Görev güncelle
- `DELETE /api/tasks/{id}` - Görev sil
- `GET /api/notifications` - Bildirimleri listele
- `PUT /api/notifications/{id}/read` - Bildirim okundu işaretle
- `GET /api/daily-summary` - Daily standup özeti
- `GET /api/dashboard/stats` - Dashboard istatistikleri

## Database Schema (SQLite)
- **users**: id, name, device_id, categories (JSON), created_at
- **tasks**: id, title, description, category_id, project_id, user_id, status (backlog/today_planned/in_progress/blocked/completed), priority, due_date, created_at, completed_at
- **projects**: id, name, description, user_id, created_at
- **notifications**: id, user_id, title, message, type, is_read, created_at

## Test Reports
- `/app/test_reports/iteration_4.json` - En son test sonuçları (%100 başarı)
- `/app/backend/tests/test_qa_task_manager.py` - Pytest test dosyası

## Prioritized Backlog

### P0 (Critical) - TAMAMLANDI
- [x] Tüm temel özellikler

### P1 (High) - Gelecek
- [ ] Görev hatırlatıcıları (push notification)
- [ ] Görev tekrarlama özelliği (haftalık regresyon için)
- [ ] Takım görünümü (tüm ekip görevleri)

### P2 (Medium) - Gelecek
- [ ] Görev yorumları ve aktivite geçmişi
- [ ] Ekip içi görev paylaşımı
- [ ] Export/Import özelliği (Excel, CSV)
- [ ] Dosya ekleri

## Notes
- MongoDB'den SQLite'a geçildi (kolay kurulum için)
- E-posta tabanlı auth kaldırıldı, cihaz tabanlı auth eklendi
- "Made with Emergent" badge JS observer ile kaldırıldı

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
- [x] **Görev Atama Sistemi** - Ekip arkadaşlarına görev atama özelliği eklendi
  - Tüm kullanıcılar listesi (/api/users)
  - Görev formunda "Atanan Kişi" alanı
  - Atama filtresi (Tüm Görevler, Kendi Görevlerim, Bana Atananlar, Atadıklarım)
  - Atama yapıldığında bildirim gönderimi
  - Kanban kartlarında atanan kişi gösterimi

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
- **tasks**: id, title, description, category_id, project_id, user_id, assigned_to, status (backlog/today_planned/in_progress/blocked/completed), priority, due_date, created_at, completed_at
- **projects**: id, name, description, user_id, created_at
- **notifications**: id, user_id, title, message, type, is_read, created_at

## Bug Fixes (29 Ocak 2026)
- [x] **Admin Panel Hatası** - `/users/roles` endpoint'i route sıralaması düzeltildi (artık `/users/{user_id}`'dan önce tanımlı)
- [x] **Rapor Dışa Aktarma Hatası** - `/reports/export` endpoint'i Pydantic model ile request body kabul edecek şekilde güncellendi
- [x] **Görev Atama Listesi** - Sadece giriş yapmış kullanıcılar listede görünüyor

## Yeni Özellikler (29 Ocak 2026)
- [x] **Rol Bazlı Erişim Kontrolü (RBAC)** - Admin, Manager, User rolleri
- [x] **Admin Panel** - Kullanıcı yönetimi ve audit logları
- [x] **Rapor Dışa Aktarma** - PDF, Excel, Word formatlarında profesyonel raporlar
- [x] **Denetim Kayıtları (Audit Logs)** - Önemli işlemlerin loglanması
- [x] **Jira Entegrasyonu** - Backend altyapısı hazır (VPN erişimi gerekli)
- [x] **Gerçek Zamanlı Bildirimler** - SSE ile anlık bildirim gönderimi

## API Endpoints (Güncel)
- `POST /api/auth/register` - Yeni kullanıcı kaydı
- `GET /api/auth/check/{device_id}` - Cihaz kontrolü
- `GET /api/users` - Görev atama için kullanıcı listesi
- `GET /api/users/roles?admin_user_id={id}` - Admin: Rol yönetimi için kullanıcılar
- `POST /api/users/assign-role` - Admin: Kullanıcı rolü atama
- `GET /api/audit-logs` - Admin/Manager: Denetim kayıtları
- `POST /api/reports/export` - Rapor dışa aktarma (PDF, Excel, Word)
- `GET /api/tasks` - Görevleri listele
- `POST /api/tasks` - Görev oluştur
- `PUT /api/tasks/{id}` - Görev güncelle
- `DELETE /api/tasks/{id}` - Görev sil
- `GET /api/notifications` - Bildirimleri listele
- `GET /api/notifications/stream` - SSE bildirim akışı
- `GET /api/jira/issues` - Jira görevleri (MOCKED - VPN gerekli)
- `POST /api/jira/sync` - Jira senkronizasyonu (MOCKED - VPN gerekli)

## Test Reports
- `/app/test_reports/iteration_5.json` - En son test sonuçları (%100 başarı - 29 Ocak 2026)
- `/app/backend/tests/test_bug_fixes.py` - Bug fix testleri
- `/app/backend/tests/test_qa_task_manager.py` - Genel testler

## Database Schema (SQLite)
- **users**: id, name, email, device_id, categories (JSON), role, created_at, password_hash
- **tasks**: id, title, description, category_id, project_id, user_id, assigned_to, status, priority, due_date, created_at, completed_at
- **projects**: id, name, description, user_id, created_at
- **notifications**: id, user_id, title, message, type, is_read, created_at
- **audit_logs**: id, user_id, action, resource_type, resource_id, details, ip_address, created_at
- **jira_tasks_cache**: id, user_id, jira_key, jira_id, summary, description, status, priority, last_synced
- **user_jira_mapping**: id, user_id, jira_username, jira_email, jira_account_id, last_synced

## Prioritized Backlog

### P0 (Critical) - TAMAMLANDI
- [x] Tüm temel özellikler
- [x] Admin Panel bug fix
- [x] Rapor export bug fix

### P1 (High) - Beklemede
- [ ] **Jira Otomatik Senkronizasyonu** - VPN erişimi olan production ortamında test edilmeli
- [ ] Görev hatırlatıcıları (push notification)
- [ ] Görev tekrarlama özelliği (haftalık regresyon için)

### P2 (Medium) - Gelecek
- [ ] Takım görünümü (tüm ekip görevleri)
- [ ] Görev yorumları ve aktivite geçmişi
- [ ] Dosya ekleri
- [ ] Gelişmiş filtreleme ve arama

## MOCKED API'ler
- **Jira Entegrasyonu**: Backend kodu hazır ancak VPN erişimi olmadığı için test edilemiyor. Production ortamında test edilmeli.

## Notes
- MongoDB'den SQLite'a geçildi (kolay kurulum için)
- E-posta tabanlı auth kaldırıldı, cihaz tabanlı auth eklendi
- "Made with Emergent" badge JS observer ile kaldırıldı
- Jira entegrasyonu için kullanıcının PAT (Personal Access Token) oluşturması gerekiyor
- SERCANO kullanıcısı varsayılan admin olarak atanıyor

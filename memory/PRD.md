# QA Hub - Product Requirements Document

## Proje Özeti
"QA Task Manager" ve "Baba Script Manager" uygulamalarını birleştiren, localhost üzerinde VPN ile çalışan QA yönetim platformu.

## Kullanıcı Gereksinimleri
1. Jira entegrasyonu (jira.intertech.com.tr)
2. MSSQL veritabanı bağlantısı (WIPREDB31.intertech.com.tr)
3. Modern, koyu temalı, soldan menülü arayüz
4. Dinamik proje ve cycle yönetimi
5. Test Kapsam Ağacı (Product Tree)
6. Gelişmiş görsel raporlama
7. **Güvenli Yönetici Paneli (Ekip Takibi)** - Kalite ekibinin görev durumlarını izleme

## Mimari
- **Frontend:** React + TailwindCSS + Shadcn/UI + Recharts
- **Backend:** FastAPI (Python)
- **Veritabanı:** SQLite (yerel), MSSQL (harici)
- **Dosyalar:** JSON (projeler, cycle'lar)

## Tamamlanan Özellikler

### 30.01.2026 - Ekip Takibi Panosu (v2.5.0)
- ✅ **Kapsamlı Yönetici Panosu:** Tüm "kalite güvence" ekibini listeleyen tablo
- ✅ **Görev İstatistikleri:** Her kullanıcı için Backlog, In Progress, Completed sayıları
- ✅ **Tarih Filtreleri:** 1, 3, 6, 12 aylık periyot seçenekleri
- ✅ **Kullanıcı Detay Modal:** Tıklandığında görev detaylarını tabs ile gösterim
- ✅ **Cancelled Görevler Hariç:** Tüm hesaplamalardan iptal edilen görevler çıkarıldı
- ✅ **Özet Kartlar:** Toplam ekip üyesi, backlog, devam eden, tamamlanan sayıları
- ✅ **Admin Doğrulama:** Güvenli giriş sistemi korundu

### 30.01.2026 (Önceki)
- ✅ Jira ve MSSQL bağlantı sorunları çözüldü
- ✅ SSE ClientDisconnect hataları düzeltildi
- ✅ Product Tree (Test Kapsam Ağacı) eklendi
- ✅ Raporlar sayfası yeniden tasarlandı (recharts)
- ✅ PDF ve Excel export modernleştirildi + Türkçe karakter desteği
- ✅ Öncelik Dağılımı UI düzeltildi
- ✅ Raporlama API'si SQLite uyumlu hale getirildi

## Bekleyen Doğrulamalar
- ⏳ Jira Araçları (Bug Bağla, Cycle Add, Jira Generator, API Rerun)

## Bilinen Kısıtlamalar
- Raporlama sayfası sadece SQLite'a kaydedilen görevleri gösteriyor
- Jira'dan çekilen görevler geçici cache'te, kalıcı kaydedilmiyor
- Jira entegrasyonu VPN bağlantısı gerektirir

## Gelecek Görevler
- P2: Platforma özel ikonlar (iOS/Android)
- P2: UI animasyonları (framer-motion)
- P3: server.py refactoring (routes klasörüne bölme)
- P3: Jira görevlerinin kalıcı kaydedilmesi (opsiyonel)

## Yeni API Endpoint'leri (Ekip Takibi)
- POST /api/admin/verify-key - Admin doğrulama
- GET /api/admin/team-summary - Ekip özet verileri (months parametresi)
- GET /api/admin/user-tasks-detail - Kullanıcı görev detayları
- GET /api/admin/qa-team - Kalite güvence ekibi listesi

## Mevcut API Endpoint'leri
- GET /api/reports/detailed-stats - Raporlama verileri (SQLite)
- POST /api/product-tree/run - Kapsam ağacı analizi
- GET /api/jira/issues - Jira görevleri
- POST /api/analysis/analyze - Test analizi

## Dosya Referansları
- `/app/frontend/src/pages/TeamTracking.jsx` - Ekip Takibi Panosu (YENİ)
- `/app/frontend/src/pages/Reports.jsx` - Raporlar sayfası
- `/app/backend/server.py` - Ana backend (admin endpoint'leri satır 3945+)
- `/app/backend/report_exporter.py` - PDF/Excel export (Türkçe destekli)
- `/app/backend/jira_api_client.py` - Jira entegrasyonu

## Admin Erişimi
- **Yöntem:** Sidebar'daki sürüm numarasına 5 kez tıkla
- **Şifre:** `server.py` içinde `_sys_cfg_v2` değişkeninde saklanıyor
- **Güvenlik:** GitHub'a yüklense bile şifre gizli kalır

## Test Dosyaları
- `/app/backend/tests/test_admin_team_tracking.py` - Admin API testleri

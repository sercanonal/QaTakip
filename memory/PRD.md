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

## Mimari
- **Frontend:** React + TailwindCSS + Shadcn/UI + Recharts
- **Backend:** FastAPI (Python)
- **Veritabanı:** SQLite (yerel), MSSQL (harici)
- **Dosyalar:** JSON (projeler, cycle'lar)

## Tamamlanan Özellikler (30.01.2026)
- ✅ Jira ve MSSQL bağlantı sorunları çözüldü
- ✅ SSE ClientDisconnect hataları düzeltildi
- ✅ Product Tree (Test Kapsam Ağacı) eklendi
- ✅ Raporlar sayfası yeniden tasarlandı (recharts)
- ✅ PDF ve Excel export modernleştirildi + Türkçe karakter desteği
- ✅ Öncelik Dağılımı UI düzeltildi (çerçeve kaldırıldı)
- ✅ Raporlama API'si SQLite uyumlu hale getirildi

## Bekleyen Doğrulamalar
- ⏳ Jira Araçları (Bug Bağla, Cycle Add, Jira Generator, API Rerun)

## Bilinen Kısıtlamalar
- Raporlama sayfası sadece SQLite'a kaydedilen görevleri gösteriyor
- Jira'dan çekilen görevler geçici cache'te, kalıcı kaydedilmiyor

## Gelecek Görevler
- P2: Platforma özel ikonlar (iOS/Android)
- P2: UI animasyonları (framer-motion)
- P3: server.py refactoring
- P3: Jira görevlerinin kalıcı kaydedilmesi (opsiyonel)

## Önemli API Endpoint'leri
- GET /api/reports/detailed-stats - Raporlama verileri (SQLite)
- POST /api/product-tree/run - Kapsam ağacı analizi
- GET /api/jira/issues - Jira görevleri
- POST /api/analysis/analyze - Test analizi

## Dosya Referansları
- `/app/frontend/src/pages/Reports.jsx` - Raporlar sayfası
- `/app/backend/server.py` - Ana backend
- `/app/backend/report_exporter.py` - PDF/Excel export (Türkçe destekli)
- `/app/backend/jira_api_client.py` - Jira entegrasyonu

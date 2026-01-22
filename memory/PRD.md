# QA Task Manager - Intertech

## Problem Statement
Intertech şirketinde QA mühendisleri için profesyonel iş takip uygulaması. Yoğun dönemlerde işlerin unutulmasını, karıştırılmasını veya tekrar yapılmasını önlemek için tasarlanmıştır.

## User Personas
- **Birincil**: QA Mühendisleri (API testi, UI testi, regresyon testleri)
- **İkincil**: Tüm Intertech çalışanları

## Core Requirements (Static)
- Şifresiz giriş sistemi (sadece @intertech.com.tr e-postası)
- Görev yönetimi (CRUD, durum, öncelik, kategori)
- Proje bazlı gruplandırma
- Haftalık takvim görünümü
- İlerleme raporları ve dashboard
- Özelleştirilebilir kategoriler
- Türkçe arayüz

## Architecture
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + Tailwind CSS + Shadcn/UI
- **Auth**: E-posta tabanlı (şifresiz), sadece @intertech.com.tr

## What's Implemented (22 Ocak 2025)
- [x] Şirket e-postası ile kayıt/giriş sistemi
- [x] Dashboard (istatistikler, son görevler, hızlı işlemler)
- [x] Görev yönetimi (oluştur, düzenle, sil, durum değiştir)
- [x] Proje yönetimi (oluştur, düzenle, sil)
- [x] Takvim görünümü (tarih bazlı görevler)
- [x] Raporlar sayfası (grafikler, istatistikler)
- [x] Ayarlar (kategori yönetimi)
- [x] Responsive sidebar navigasyon
- [x] Dark mode tasarım

## Prioritized Backlog
### P0 (Critical) - TAMAMLANDI
- Tüm temel özellikler implementasyonları

### P1 (High)
- E-posta bildirimleri (SendGrid/Resend entegrasyonu)
- Görev hatırlatıcıları
- Drag & drop ile görev sıralama

### P2 (Medium)
- Görev yorumları ve aktivite geçmişi
- Ekip içi görev paylaşımı
- Export/Import özelliği

## Next Tasks
1. E-posta bildirim sistemi eklenebilir (kullanıcı isteği üzerine)
2. Görev tekrarlama özelliği (haftalık regresyon için)
3. Takım görünümü (tüm ekip görevleri)

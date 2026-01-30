#!/bin/bash
# QA Hub - Tek Komutla Kurulum ve Başlatma (Mac)
# Kullanım: ./start.sh

echo "╔════════════════════════════════════════╗"
echo "║   🚀 QA Hub - Kurulum Başlatılıyor    ║"
echo "╚════════════════════════════════════════╝"

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Proje kök dizini
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo -e "${YELLOW}📁 Proje dizini: $PROJECT_DIR${NC}"

# ============== FRONTEND .ENV OLUŞTUR ==============
echo ""
echo -e "${YELLOW}📝 Frontend .env dosyası oluşturuluyor...${NC}"
cat > "$PROJECT_DIR/frontend/.env" << 'EOF'
# Backend API URL - Localhost
REACT_APP_BACKEND_URL=http://localhost:8001
EOF
echo -e "${GREEN}✅ Frontend .env oluşturuldu${NC}"

# ============== BACKEND KURULUM ==============
echo ""
echo -e "${YELLOW}🐍 Backend kurulumu başlatılıyor...${NC}"
cd "$PROJECT_DIR/backend"

# Virtual environment kontrolü
if [ ! -d "venv" ]; then
    echo "   📦 Virtual environment oluşturuluyor..."
    python3 -m venv venv
fi

# Aktive et
source venv/bin/activate

# Bağımlılıkları yükle
echo "   📦 Python paketleri yükleniyor..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# openpyxl ekle (opsiyonel ama uyarıyı kaldırır)
pip install -q openpyxl 2>/dev/null || true

echo -e "${GREEN}✅ Backend kurulumu tamamlandı${NC}"

# ============== FRONTEND KURULUM ==============
echo ""
echo -e "${YELLOW}⚛️  Frontend kurulumu başlatılıyor...${NC}"
cd "$PROJECT_DIR/frontend"

# node_modules kontrolü
if [ ! -d "node_modules" ]; then
    echo "   📦 npm paketleri yükleniyor (bu biraz sürebilir)..."
    npm install --silent
fi

echo -e "${GREEN}✅ Frontend kurulumu tamamlandı${NC}"

# ============== UYGULAMAYI BAŞLAT ==============
echo ""
echo "╔════════════════════════════════════════╗"
echo "║   🚀 Uygulama Başlatılıyor...         ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Backend'i arka planda başlat
cd "$PROJECT_DIR/backend"
source venv/bin/activate

echo -e "${YELLOW}🔧 Backend başlatılıyor (port 8001)...${NC}"
# Eski process'i öldür
pkill -f "uvicorn server:app" 2>/dev/null || true
sleep 1

# Backend'i arka planda başlat
nohup uvicorn server:app --host 0.0.0.0 --port 8001 > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend başlatıldı (PID: $BACKEND_PID)${NC}"

# Backend'in başlamasını bekle
echo "   ⏳ Backend'in hazır olması bekleniyor..."
sleep 3

# Backend kontrolü
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Backend hazır!${NC}"
else
    echo -e "${YELLOW}   ⚠️  Backend henüz hazır değil, devam ediliyor...${NC}"
fi

# Frontend'i başlat
echo ""
echo -e "${YELLOW}⚛️  Frontend başlatılıyor (port 3000)...${NC}"
cd "$PROJECT_DIR/frontend"

# Eski process'i öldür
pkill -f "react-scripts start" 2>/dev/null || true
sleep 1

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🎉 QA Hub Hazır!                                        ║"
echo "║                                                            ║"
echo "║   📍 Frontend: http://localhost:3000                      ║"
echo "║   📍 Backend:  http://localhost:8001                      ║"
echo "║                                                            ║"
echo "║   👤 Giriş: SERCANO                                       ║"
echo "║                                                            ║"
echo "║   ⚠️  Kapatmak için: Ctrl+C                               ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Frontend'i foreground'da başlat
npm start

# Script sonlandığında backend'i de kapat
trap "echo ''; echo 'Kapatılıyor...'; pkill -f 'uvicorn server:app'; exit 0" SIGINT SIGTERM

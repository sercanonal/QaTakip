#!/bin/bash
# QA Hub - Tek Komutla Kurulum ve Başlatma (Mac)
# Kullanım: chmod +x start.sh && ./start.sh
# Proxy olmadan: USE_PROXY=no ./start.sh

echo "╔════════════════════════════════════════╗"
echo "║   🚀 QA Hub - Kurulum Başlatılıyor    ║"
echo "╚════════════════════════════════════════╝"

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Proje kök dizini
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo -e "${YELLOW}📁 Proje dizini: $PROJECT_DIR${NC}"

# ============== PORT TEMİZLİĞİ ==============
echo ""
echo -e "${YELLOW}🧹 Eski process'ler temizleniyor...${NC}"

# Port 3000 temizle
lsof -ti :3000 2>/dev/null | xargs -r kill -9 2>/dev/null || true
# Port 8001 temizle  
lsof -ti :8001 2>/dev/null | xargs -r kill -9 2>/dev/null || true
# Eski uvicorn process'lerini temizle
pkill -f "uvicorn server:app" 2>/dev/null || true
# Eski react process'lerini temizle
pkill -f "react-scripts start" 2>/dev/null || true
pkill -f "craco start" 2>/dev/null || true

sleep 2
echo -e "${GREEN}✅ Portlar temizlendi${NC}"

# ============== FRONTEND .ENV OLUŞTUR ==============
echo ""
echo -e "${YELLOW}📝 Frontend .env dosyası oluşturuluyor...${NC}"

# Önce eski .env'i sil ve yenisini oluştur
rm -f "$PROJECT_DIR/frontend/.env"
cat > "$PROJECT_DIR/frontend/.env" << 'EOF'
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_API_URL=http://localhost:8001
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

# Her zaman npm install yap (cache sorunu çözümü için)
echo "   📦 npm paketleri yükleniyor..."
npm install --legacy-peer-deps 2>/dev/null || npm install

# npm cache temizle (opsiyonel ama .env sorunlarını çözebilir)
npm cache clean --force 2>/dev/null || true

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

# Backend'i arka planda başlat
nohup uvicorn server:app --host 0.0.0.0 --port 8001 > "$PROJECT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend başlatıldı (PID: $BACKEND_PID)${NC}"

# Backend'in başlamasını bekle
echo "   ⏳ Backend'in hazır olması bekleniyor..."
sleep 5

# Backend kontrolü
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Backend hazır!${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   ⏳ Backend bekleniyor... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}   ❌ Backend başlatılamadı! backend.log dosyasını kontrol edin.${NC}"
    cat "$PROJECT_DIR/backend.log" | tail -20
    exit 1
fi

# Frontend'i başlat
echo ""
echo -e "${YELLOW}⚛️  Frontend başlatılıyor (port 3000)...${NC}"
cd "$PROJECT_DIR/frontend"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║   🎉 QA Hub Hazır!                                        ║"
echo "║                                                            ║"
echo "║   📍 Frontend: http://localhost:3000                      ║"
echo "║   📍 Backend:  http://localhost:8001                      ║"
echo "║                                                            ║"
echo "║   👤 Giriş: Kullanıcı adınızı yazın (örn: SERCANO)        ║"
echo "║                                                            ║"
echo "║   ⚠️  Kapatmak için: Ctrl+C                               ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Trap ile cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Kapatılıyor...${NC}"
    pkill -f "uvicorn server:app" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    pkill -f "craco start" 2>/dev/null || true
    lsof -ti :3000 2>/dev/null | xargs -r kill -9 2>/dev/null || true
    lsof -ti :8001 2>/dev/null | xargs -r kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ Kapatıldı${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Frontend'i foreground'da başlat
npm start

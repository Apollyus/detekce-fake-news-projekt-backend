# 🔍 Detekce Fake News - Backend API

Backend pro projekt bezfejku.cz. Cílem této aplikace je ověřování fake news pomocí umělé inteligence. 

## 📋 Přehled projektu

Tato aplikace poskytuje RESTful API pro:
- **Detekci fake news** pomocí AI modelů (OpenAI, Mistral, OpenRouter)
- **Ověřování faktů** prostřednictvím Google Search API
- **Uživatelskou autentizaci** přes Google OAuth
- **Rate limiting** a telemetrii pro monitoring

## 🚀 Jak spustit projekt

Před samotným pokusem o spuštění je potřeba vytvořit .env soubor se všemy potřebnými proměnnými.

```bash

Nejjednodušší způsob spuštění pomocí Docker Compose:

```bash
# Naklonování repozitáře
git clone https://github.com/Apollyus/detekce-fake-news-projekt-backend.git
cd detekce-fake-news-projekt-backend

# Spuštění všech služeb
docker-compose up --build
```

**Služby budou dostupné na:**
- 🌐 **Backend API**: http://localhost:8000
- 📖 **Dokumentace API**: http://localhost:8000/docs
- 🗄️ **pgAdmin**: http://localhost:5050 
- 💾 **PostgreSQL**: localhost:5432

### Připojení k databázi

**Z vašeho počítače:**
- Hostitel: `db`
- Port: `5432`
- Databáze: `bezfejku_db`
- Uživatelské jméno: `postgres`
- Heslo: `postgres`

## 🎯 Endpointy API

### Základní analýza
```http
GET /api/v1/{prompt}
GET /api/v1?prompt=text_k_analyze
```

### Detekce fake news
```http
GET /api/v2/fake_news_check/{prompt}
GET /api/v2/fake_news_check?prompt=text_zpravy
```

### Ověření identity
```http
POST /auth/login
GET /auth/callback
POST /auth/logout
```

### Administrátorské rozhraní
```http
GET /admin/users
GET /admin/stats
```

## 🛠️ Technologie

- **API framework**: FastAPI (Python)
- **Databáze**: PostgreSQL + SQLAlchemy
- **AI modely**: OpenAI GPT, OpenRouter
- **Zpracování jazyka**: spaCy, transformers, NLTK
- **Extrakce z webu**: BeautifulSoup, breadability
- **Ověření identity**: OAuth 2.0 (Google), JWT tokeny
- **Nasazení**: Docker, Docker Compose

## 📁 Struktura projektu

```
├── docs/                   # Dokumentace
│   ├── endpoints.md        # API endpointy
│   ├── quickstart.md       # Rychlý start
│   └── rate_limits.md      # Omezení rychlosti
├── source/
│   ├── app.py              # Hlavní FastAPI aplikace
│   ├── modules/            # Základní moduly
│   │   ├── config.py       # Konfigurace
│   │   ├── database.py     # Databázové připojení
│   │   ├── models.py       # SQLAlchemy modely
│   │   └── ...
│   ├── routes/             # Endpointy API
│   │   ├── fake_news_routes.py
│   │   ├── auth_routes.py
│   │   └── ...
│   └── middleware/         # Middleware pro omezení rychlosti
├── main.py                 # Vstupní bod aplikace
├── init_db.py             # Inicializace databáze
├── docker-compose.yml     # Konfigurace Dockeru
├── requirements.txt       # Python závislosti
└── .env                   # Proměnné prostředí
```

## 🔧 Užitečné příkazy

```bash
# Zobrazení běžících kontejnerů
docker ps

# Zobrazení logů
docker-compose logs backend
docker-compose logs db

# Restart služeb
docker-compose restart

# Zastavení a vyčištění
docker-compose down -v

# Spuštění na pozadí
docker-compose up -d
```

## 🐛 Řešení problémů

### Databáze není dostupná
Ujistěte se, že PostgreSQL kontejner běží a porty jsou správně namapované.

### AI API nefungují
Zkontrolujte platnost API klíčů v souboru `.env`.

### Port je již používán
Změňte porty v `docker-compose.yml` nebo zastavte konfliktní služby.

## 📚 Další dokumentace

- 📖 **[Kompletní API dokumentace](docs/endpoints.md)** - Detailní popis všech endpointů
- ⚡ **[Rychlý start](docs/quickstart.md)** - 1-minutové nastavení projektu
- 🚫 **[Omezení rychlosti](docs/rate_limits.md)** - Pravidla pro API volání

---

**Autor**: Apollyus  
**Repozitář**: https://github.com/Apollyus/detekce-fake-news-projekt-backend
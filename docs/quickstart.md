# ⚡ Rychlý start

Pokud se chcete rychle dostat k funkčnímu systému:

## 🚀 1 minuta nastavení

```bash
# 1. Naklonování repozitáře
git clone https://github.com/Apollyus/detekce-fake-news-projekt-backend.git
cd detekce-fake-news-projekt-backend

# 2. Spuštění aplikace
docker-compose up --build
```

## ✅ Ověření funkčnosti

Po spuštění otevřete v prohlížeči:

1. **Backend API**: http://localhost:8000
   - Měli byste vidět: `{"message": "Hello, World!"}`

2. **Dokumentace API**: http://localhost:8000/docs
   - Interaktivní Swagger UI se všemi endpointy

3. **pgAdmin**: http://localhost:5050
   - Přihlášení: `admin@example.com` / `admin123`

## 🧪 Testování API

### Základní test
```bash
curl http://localhost:8000/
```

### Test detekce fake news
```bash
curl "http://localhost:8000/api/v2/fake_news_check/Testovací%20zpráva"
```

### Test pomocí Swagger UI
Jděte na http://localhost:8000/docs a vyzkoušejte endpointy přímo v prohlížeči.

## 🔧 Pokud něco nefunguje

1. **Kontejnery neběží**: `docker-compose ps`
2. **Chyba portů**: Změňte porty v `docker-compose.yml`
3. **Chybí API klíče**: Zkontrolujte `.env` soubor
4. **Zobrazení logů**: `docker-compose logs backend`

---
Více informací v [README.md](../README.md)

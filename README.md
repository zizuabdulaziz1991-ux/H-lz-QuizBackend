# Hızlı Quiz – Backend

Django 5 + DRF REST API. Ayrıntılı tasarım: `docs/`.

## Yerel çalıştırma

```bash
python -m venv .venv && .venv/Scripts/activate   # Python 3.12/3.13 önerilir
pip install -r requirements/dev.txt
cp .env.example .env                              # DATABASE_URL boşsa SQLite kullanılır
python manage.py migrate
python manage.py import_questions                 # data/questions.json
python manage.py createsuperuser
python manage.py runserver
pytest
```

Docker ile (Postgres dahil): `docker compose -f docker/docker-compose.yml up --build` → http://localhost:8000/api/docs/

## Önemli adresler

| Adres | Açıklama |
| --- | --- |
| `/api/v1/...` | REST API |
| `/api/docs/` | Swagger UI (OpenAPI: `/api/schema/`) |
| `/admin/` | Soru yönetimi |
| `/healthz` | Sağlık kontrolü |

## Notlar

- Süre aşımı: geç gelen cevap hata dönmez; `200` + `timed_out: true`, 0 puan olarak kaydedilir.
- Soru sırası/şık sırası sunucuda belirlenir; doğru şık yalnızca cevaptan sonra döner.
- Soru eklemek: Admin panelinden veya `data/questions.json` formatında `import_questions` ile.
- Eski oturumlar: `python manage.py expire_sessions` (günlük çalıştırılmalı).
- Ayarlar ortam değişkenleriyle: bkz. `.env.example`, `config/settings/base.py`.

## Render deploy

`render.yaml` (Blueprint): Docker web servisi (`hizliquiz-backend`, Frankfurt) + Postgres 16. Açılışta `docker/start.sh`
migration çalıştırır ve soruları idempotent olarak yükler. Admin kullanıcısı için Render Shell'de
`python manage.py createsuperuser` (Shell ücretli plan ister; alternatif: ortam değişkeni + komut).

## Mobil istemciler (iOS / Android)

- Aynı `/api/v1/` sözleşmesi; `X-Client: ios|android` ve `X-App-Version: 1.2.3` başlıkları gönderilmeli.
- `GET /api/v1/config/` → `min_app_version`; altındaki sürüm oturum açarken `426 upgrade_required` alır.
- Süre çubuğu için yanıttaki `server_time` / `expires_at` kullanılmalı (cihaz saatine güvenme).
- Şema: `/api/schema/` (OpenAPI) → Swift/Kotlin/Dart istemci üretilebilir. Native uygulamalar CORS'a tabi değildir.
- Free Render planı boştayken uyur (ilk istek ~50 sn); mobil için en az `starter` planı kullanın.

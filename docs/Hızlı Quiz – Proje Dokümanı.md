# Hızlı Quiz – Proje Dokümanı

Oct 29, 2026 · @abdulazız

## 1. Proje özeti ve hedefler

Hızlı Quiz, kullanıcıların kayıt olmadan 5 kategoride, soru başına yalnızca 5 saniye süreyle bilgi yarışması oynadığı bir web uygulamasıdır; mobil sürümü aynı backend üzerinden çalışacaktır.

- **Kategoriler:** Tarih, Müzik, Coğrafya, Genel Kültür, Fizik
- **Quiz yapısı:** Seçilen kategoride 20 soru, her soru ayrı ekranda; cevaplanmadan veya süre dolmadan sonraki soru görülemez
- **Süre:** Her soru için 5 saniye (adı da buradan gelir)
- **Hesap yok:** Kayıt, giriş, kullanıcı oluşturma yok. Quiz bitince puan hesaplanır, kullanıcıdan yalnızca takma ad istenir
- **Skor tablosu:** İsim girildikten sonra Top 10 listesi gösterilir
- **Mimari hedef:** Ayrı backend ve frontend repo'ları; backend hem web hem mobil istemciye hizmet verir

**Başarı ölçütleri**

- Kullanıcı ana ekrandan quiz sonuna en fazla 4 dokunuş/tıklamayla ulaşır
- Bir quiz oturumu yaklaşık 2 dakikada tamamlanır (20 soru × 5 sn + geçişler)
- API, web ve mobil için aynı sözleşmeyi kullanır; mobil için backend'de değişiklik gerekmez

## 2. Kapsam ve fonksiyonel gereksinimler

İlk sürüm (MVP) dört ekran ve altı temel fonksiyondan oluşur; hesap yönetimi bilinçli olarak kapsam dışıdır.

| No | Gereksinim | Öncelik |
| --- | --- | --- |
| F1 | Kullanıcı 5 kategoriden birini seçer | Zorunlu |
| F2 | Seçilen kategoriden rastgele 20 soru, her biri ayrı ekranda sorulur | Zorunlu |
| F3 | Her soru için 5 saniye geri sayım; süre dolarsa soru boş geçilir ve sonraki soruya geçilir | Zorunlu |
| F4 | Cevap verilen soruda doğru/yanlış geri bildirimi gösterilir, geri dönüş yoktur | Zorunlu |
| F5 | Quiz sonunda puan hesaplanır ve isim istenir | Zorunlu |
| F6 | Kategori bazlı Top 10 skor tablosu | Zorunlu |
| F7 | Soru yönetimi için yönetici paneli (Django Admin) | Zorunlu |
| F8 | Ses/titreşim geri bildirimi, paylaşım butonu | İsteğe bağlı |

**Kapsam dışı (ilk sürüm):** kullanıcı hesabı, giriş/şifre, arkadaş listesi, çok oyunculu mod, reklam, ödeme, çoklu dil.

**Varsayımlar (onayınıza açık):** Skor tablosu her kategori için ayrı tutulur. Soru bankasında her kategori için en az 20 soru gerekir; çeşitlilik için 40+ soru önerilir, her oturumda rastgele 20 tanesi seçilir.

## 3. Kullanıcı akışı

Kullanıcı ana ekrandan kategori seçer, 20 soruyu sırayla yanıtlar, puanını görür, adını girer ve skor tablosuna ulaşır.

1. **Ana ekran:** 5 kategori kartı görünür; kullanıcı birini seçer.
2. **Hazır ol ekranı:** Kısa bir 3-2-1 geri sayımı (isteğe bağlı), ardından quiz başlar.
3. **Soru ekranı (20 kez):** Soru metni, 4 şık ve 5 saniyelik süre çubuğu. Şıka dokunulunca veya süre bitince doğru cevap kısa süre gösterilir, sonraki soruya geçilir.
4. **Sonuç ekranı:** Toplam puan, doğru sayısı ve ortalama cevap süresi.
5. **İsim girişi:** Takma ad (2–20 karakter) girilir. Atlanırsa puan skor tablosuna yazılmaz.
6. **Skor tablosu:** Kategorinin ilk 10 skoru; kullanıcının sırası vurgulanır. "Tekrar oyna" ve "Kategori değiştir" butonları bulunur.

Sayfa yenilenirse veya uygulama kapanırsa oturum devam ettirilmez; başlanmış quiz tamamlanmamış sayılır ve skora yazılmaz.

## 4. Sistem mimarisi ve teknoloji yığını

Sistem üç katmandan oluşur: istemciler (Vue.js web ve mobil uygulama), tek bir REST API (Django) ve PostgreSQL veritabanı. Web ve mobil aynı API'yi kullanır.

| Katman | Teknoloji | Not |
| --- | --- | --- |
| Web istemci | Vue 3 + Vite + TypeScript, Pinia, Vue Router, Tailwind CSS | Ayrı repo: `hizliquiz-frontend` |
| Mobil istemci | Flutter veya React Native (karar bekliyor, bkz. Bölüm 12) | Ayrı repo: `hizliquiz-mobile` |
| Backend | Python 3.12, Django 5, Django REST Framework | Ayrı repo: `hizliquiz-backend` |
| Veritabanı | PostgreSQL 16 | Django ORM + migration'lar |
| API dokümantasyonu | drf-spectacular (OpenAPI 3 / Swagger UI) | Mobil ekip sözleşmeyi buradan alır |
| Sunucu | Gunicorn + Nginx, Docker | Frontend statik olarak ayrı servis edilir |
| Önbellek (isteğe bağlı) | Redis | Skor tablosu ve rate limit için, ilk sürümde zorunlu değil |

**İstek akışı:** İstemci → HTTPS → Nginx → Gunicorn/Django (DRF) → PostgreSQL. Süre kontrolü ve puan hesabı yalnızca backend'de yapılır; istemci sadece görüntüler.

**Ortamlar:** local (Docker Compose), staging, production. Ayarlar ortam değişkenleriyle yönetilir (`.env`, 12-factor).

## 5. Veritabanı tasarımı (PostgreSQL)

Veritabanı beş tablodan oluşur; kullanıcı tablosu yoktur, her quiz anonim bir oturum (session) olarak tutulur.

| Tablo | Önemli alanlar | Açıklama |
| --- | --- | --- |
| `category` | id, slug, name, icon, color, is\_active | 5 kategori; renk ve ikon istemciye buradan gelir |
| `question` | id, category\_id, text, difficulty, is\_active, created\_at | Soru bankası |
| `choice` | id, question\_id, text, is\_correct, position | Her soru için 4 şık, yalnızca biri doğru |
| `quiz_session` | id (UUID), category\_id, status, started\_at, finished\_at, total\_score, correct\_count, player\_name (null), name\_submitted\_at, client\_type | Bir quiz oynayışı; `status`: in\_progress / finished / expired |
| `session_question` | id, session\_id, question\_id, position (1–20), served\_at, answered\_at, selected\_choice\_id (null), is\_correct, time\_taken\_ms, points | Oturumda sorulan sorular ve cevaplar |

**İlişkiler:** category 1—N question, question 1—N choice, category 1—N quiz\_session, quiz\_session 1—N session\_question.

**Skor tablosu:** Ayrı tablo yerine `quiz_session` üzerinden sorgulanır: `status = finished` ve `player_name IS NOT NULL` olan kayıtlar, kategoriye göre `total_score DESC, finished_at ASC` sıralanır, ilk 10 alınır.

**İndeksler:** `question(category_id, is_active)`, `session_question(session_id, position)` benzersiz, `quiz_session(category_id, total_score DESC, finished_at)` (kısmi indeks: yalnızca isim girilmiş kayıtlar).

**Kısıtlar:** `choice` için soru başına tam bir doğru şık; `player_name` 2–20 karakter; `client_type` değerleri: web, ios, android.

## 6. REST API tasarımı (web ve mobil için)

API, `/api/v1/` altında JSON döndüren, istemciden bağımsız bir REST arayüzüdür; hesap olmadığı için kimlik doğrulama yerine oturuma özel bir token kullanılır.

| Metot | Uç nokta | Açıklama |
| --- | --- | --- |
| GET | `/api/v1/categories/` | Kategori listesi (ad, ikon, renk, soru sayısı) |
| POST | `/api/v1/sessions/` | Gövde: `category`. Oturum açar, `session_id` ve `session_token` döner |
| GET | `/api/v1/sessions/{id}/question/` | Sıradaki soruyu verir ve 5 sn'lik süreyi sunucuda başlatır. Doğru şık bilgisi içermez |
| POST | `/api/v1/sessions/{id}/answer/` | Gövde: `question_id`, `choice_id` (süre dolduysa null). Sonuç: is\_correct, correct\_choice\_id, points |
| GET | `/api/v1/sessions/{id}/result/` | Quiz bittiğinde toplam puan, doğru sayısı, ortalama süre |
| POST | `/api/v1/sessions/{id}/submit-name/` | Gövde: `player_name`. Skoru tabloya yazar, sıralamayı döner |
| GET | `/api/v1/leaderboard/?category={slug}&limit=10` | Kategorinin Top 10 listesi |
| GET | `/api/v1/config/` | Süre (5 sn), soru sayısı (20), minimum uygulama sürümü |

**Başlıklar:** `X-Session-Token` (oturum uç noktalarında zorunlu), `X-Client: web | ios | android`, `X-App-Version`.

**Örnek soru yanıtı:**

```json
{
  "question_id": 412,
  "position": 7,
  "total": 20,
  "text": "Ay'a ilk ayak basan insan kimdir?",
  "choices": [
    {"id": 1601, "text": "Yuri Gagarin"},
    {"id": 1602, "text": "Neil Armstrong"},
    {"id": 1603, "text": "Buzz Aldrin"},
    {"id": 1604, "text": "John Glenn"}
  ],
  "time_limit_ms": 5000,
  "expires_at": "2026-10-29T18:40:05Z"
}
```

**Hata biçimi:** `{"error": {"code": "time_expired", "message": "..."}}`. Başlıca kodlar: `invalid_token`, `time_expired`, `already_answered`, `session_finished`, `invalid_name`, `rate_limited`.

**Mobil uyumluluk ilkeleri:** Sürümlü URL, geriye dönük uyumlu alan ekleme, ISO 8601 UTC zaman damgası, sayfalama gerektirmeyen küçük yanıtlar, OpenAPI şemasından otomatik istemci üretimi.

## 7. Backend (Django) yapısı

Backend, iş kurallarını (süre, puan, soru seçimi) tek yerde tutan, DRF tabanlı ve servis katmanlı bir Django projesidir.

```text
hizliquiz-backend/
├── config/                # settings (base/dev/prod), urls, wsgi
├── apps/
│   ├── quiz/              # category, question, choice, session modelleri + API
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py    # oturum başlatma, soru seçme, cevap doğrulama, puan hesabı
│   │   ├── views.py
│   │   └── tests/
│   └── leaderboard/       # skor tablosu sorguları ve endpoint'i
├── fixtures/ veya data/   # başlangıç soruları (JSON/CSV)
├── docker/                # Dockerfile, docker-compose.yml
├── requirements/          # base.txt, dev.txt, prod.txt
└── manage.py
```

**Paketler:** djangorestframework, psycopg (v3), django-cors-headers, drf-spectacular, django-environ, gunicorn, whitenoise; test için pytest-django ve factory-boy.

**Temel kararlar**

- İş mantığı `services.py` içinde; view'lar ince kalır, testler servisleri hedefler.
- Oturum başladığında kategoriden 20 rastgele aktif soru seçilir ve `session_question` satırları sıralı oluşturulur.
- Soru servis edilirken `served_at` kaydedilir; cevap geldiğinde sunucu süresini kontrol eder (bkz. Bölüm 10).
- Django Admin üzerinden soru, şık ve kategori yönetimi; toplu içe aktarma için `import_questions` management komutu (CSV/JSON).
- Süresi dolup bitmeyen oturumlar için günlük temizlik komutu (ör. 24 saatten eski `in_progress` kayıtları `expired` yapılır).

## 8. Frontend (Vue.js) yapısı

Frontend, dört ekranlı bir tek sayfa uygulamasıdır (SPA); tüm veriyi API'den alır ve durumu Pinia ile yönetir.

| Ekran | Rota | İçerik |
| --- | --- | --- |
| Ana ekran | `/` | 5 kategori kartı, "Skor tablosu" bağlantısı |
| Quiz | `/quiz/:sessionId` | Soru, 4 şık, süre çubuğu, ilerleme (7/20), canlı puan |
| Sonuç | `/result/:sessionId` | Puan özeti, isim girişi |
| Skor tablosu | `/leaderboard/:category?` | Kategori sekmeleri, Top 10 |

```text
hizliquiz-frontend/
├── src/
│   ├── api/          # fetch/axios istemcisi, endpoint fonksiyonları
│   ├── stores/       # quiz.ts (oturum, soru, süre), leaderboard.ts
│   ├── views/        # Home, Quiz, Result, Leaderboard
│   ├── components/   # CategoryCard, QuestionCard, AnswerButton, TimerBar, ScoreList
│   ├── router/
│   └── assets/       # fontlar, ikonlar, global stiller
├── .env.example      # VITE_API_BASE_URL
└── vite.config.ts
```

**Quiz ekranı mantığı**

1. Ekran açılınca `GET .../question/` çağrılır; yanıttaki `expires_at` süre çubuğunun kaynağıdır.
2. Geri sayım `requestAnimationFrame` ile akıcı çizilir; sunucu saatine göre düzeltilir.
3. Şık seçilince butonlar kilitlenir, `POST .../answer/` gönderilir, doğru/yanlış rengi gösterilir (yaklaşık 1 sn).
4. Süre biterse otomatik olarak `choice_id: null` gönderilir.
5. Soru 20 ise sonuç ekranına yönlendirilir.

**Diğer:** Geri tuşu quiz içinde devre dışı bırakılır (uyarı gösterilir); ağ hatasında tek yeniden deneme ve "bağlantı koptu" ekranı; erişilebilirlik için klavye kısayolları (1–4) ve yeterli renk kontrastı.

## 9. UI/UX tasarım rehberi

Tasarım dili genç, enerjik ve canlıdır: açık zemin, doygun ana renkler, yuvarlak köşeler ve büyük dokunma alanları kullanılır; koyu tema ilk sürümde yoktur.

**Renk paleti (öneri)**

| Rol | Renk | Hex |
| --- | --- | --- |
| Zemin | Açık lavanta | `#F7F5FF` |
| Ana renk | Canlı mor | `#6C5CE7` |
| Vurgu | Pembe | `#FF5CA8` |
| Doğru cevap | Nane yeşili | `#2ED8A7` |
| Yanlış cevap | Mercan kırmızısı | `#FF5C6C` |
| Metin | Koyu lacivert | `#2B2D42` |

**Kategori renkleri**

| Kategori | Renk | Hex |
| --- | --- | --- |
| Tarih | Turuncu | `#FF8A3D` |
| Müzik | Pembe | `#FF5CA8` |
| Coğrafya | Yeşil | `#2ED8A7` |
| Genel Kültür | Sarı | `#FFC93C` |
| Fizik | Mavi | `#3DA5FF` |

**Tipografi:** Başlıklarda Poppins (700), gövdede Nunito; Türkçe karakter desteği doğrulanmalıdır.

**Bileşen ilkeleri**

- Köşe yuvarlaklığı 20–24 px, yumuşak gölgeler, kartlarda kategori renginde gradyan.
- Şık butonları tam genişlikte ve en az 56 px yüksekliğinde (mobilde tek elle kullanım).
- Süre çubuğu ekranın üstünde; son 2 saniyede renk yeşilden turuncuya/kırmızıya döner ve hafif titrer.
- Doğru/yanlış için renk + ikon birlikte kullanılır (yalnızca renge güvenilmez).
- Mikro animasyonlar: kart geçişi, puan sayacı, konfeti (yeni Top 10 girişinde).
- Skor tablosunda ilk 3 sıra madalya ikonlarıyla vurgulanır.

Tasarım Figma'da hazırlanmalı; renk ve boşluk değerleri tasarım token'ı olarak hem web (Tailwind config) hem mobilde ortak kullanılmalıdır.

## 10. Puanlama ve süre kuralları

Süre ve puan yalnızca sunucuda hesaplanır; hızlı cevap ek puan kazandırır ve en yüksek skor 3.000'dir (öneri, ayarlanabilir).

| Durum | Puan |
| --- | --- |
| Doğru cevap | 100 |
| Hız bonusu | 0–50 (kalan süreyle orantılı) |
| Yanlış cevap | 0 |
| Süre doldu / cevap yok | 0 |

```latex
Puan = 100 + 50 \times \frac{5000 - t_{ms}}{5000}
```

Burada t, sorunun sunucuda gösterildiği an ile cevabın alındığı an arasındaki süredir (milisaniye). Maksimum: 20 × 150 = 3.000 puan.

**Süre kuralları**

- Sorunun süresi, soru `GET` ile verildiği anda sunucuda başlar (`served_at`).
- Cevap, `served_at + 5 sn + 1 sn ağ toleransı` içinde gelmezse süre dolmuş sayılır ve 0 puan verilir.
- Aynı soruya ikinci cevap kabul edilmez (`already_answered`).
- Soru sırası atlanamaz: sunucu yalnızca bir sonraki cevapsız soruyu verir.
- Eşitlikte skor tablosunda önce daha erken tamamlayan üstte yer alır.

Süre, puan formülü ve soru sayısı `GET /config/` ile istemciye bildirilir; değerler sunucuda değiştirilebilir.

## 11. Güvenlik ve kötüye kullanım önlemleri

Hesap olmadığı için en büyük risk, sahte skor gönderimi ve skor tablosunun spam'lenmesidir; bu yüzden tüm doğrulama sunucuda yapılır.

| Risk | Önlem |
| --- | --- |
| Doğru cevabın istemciden okunması | Soru yanıtında `is_correct` alanı gönderilmez; doğru şık yalnızca cevaptan sonra döner |
| Süreyi istemcide uzatma | Süre sunucu saatiyle ölçülür, istemci zamanı dikkate alınmaz |
| Sahte skor gönderme | Puan istemciden alınmaz; backend cevaplardan hesaplar |
| Bot ile toplu oturum açma | IP başına rate limit (DRF throttling), oturum başına tek isim gönderimi |
| Uygunsuz takma adlar | Uzunluk ve karakter doğrulaması, küfür/hakaret filtresi (Türkçe kelime listesi), admin panelinden gizleme |
| Oturum tokenının çalınması | Rastgele ve tahmin edilemez UUID + token; yalnızca HTTPS |
| Genel web riskleri | CORS izin listesi, `DEBUG=False`, gizli anahtarlar ortam değişkeninde, Django güvenlik başlıkları |
| Veri kaybı | PostgreSQL için günlük otomatik yedek |

**Kişisel veri (KVKK):** Yalnızca takma ad ve oyun sonuçları saklanır; e-posta, telefon veya kimlik bilgisi toplanmaz. Uygulamada kısa bir gizlilik notu bulunmalı ve ismin herkese açık skor tablosunda görüneceği isim girişinde belirtilmelidir. Mobil mağazalar gizlilik politikası URL'si isteyecektir.

## 12. Mobil uygulama hazırlığı

Backend baştan istemciden bağımsız tasarlandığı için mobil uygulama aynı API'yi kullanır; ek backend işi yalnızca sürüm yönetimi ve mağaza gereksinimleriyle sınırlıdır.

- **Aynı sözleşme:** Web ve mobil aynı `/api/v1/` uç noktalarını kullanır; istemci `X-Client` başlığıyla ayrışır.
- **OpenAPI:** drf-spectacular çıktısından mobil istemci kodu üretilebilir.
- **Sürüm kontrolü:** `GET /config/` içindeki `min_app_version` ile eski uygulama sürümleri güncellemeye yönlendirilir.
- **Kırıcı değişiklik:** Gerekirse `/api/v2/` açılır; v1 mobil kullanıcılar güncelleyene kadar çalışmaya devam eder.
- **Zaman senkronu:** Sunucu zamanı yanıtlarda döner; mobil süre çubuğu bu zamana göre düzeltilir (cihaz saati yanlış olabilir).
- **Ağ koşulları:** Mobil ağ gecikmesi için 1 sn tolerans korunur; kopma halinde oturum yeniden başlatılır.
- **Tasarım:** Renk, tipografi ve bileşen kuralları Bölüm 9'daki token'lardan paylaşılır.

**Açık karar:** Mobil teknoloji seçimi. Ekipte Vue/JavaScript deneyimi ağırlıksa React Native (veya Vue bilgisini kısmen kullanan Capacitor ile web'i sarmalama); tek kod tabanı ve güçlü animasyon önceliğiyse Flutter önerilir. Karar mobil geliştirme başlamadan önce verilmelidir.

## 13. Test, dağıtım ve yol haritası

MVP web sürümü yaklaşık 6 haftada çıkarılabilir; mobil uygulama bunun ardından başlar (süreler tahmindir, ekip büyüklüğüne göre değişir).

| Faz | İçerik | Tahmini süre |
| --- | --- | --- |
| 0. Hazırlık | Repo'lar, Docker Compose, CI, Figma tasarımı, soru bankası yazımı (5 × 40 soru) | 1 hafta |
| 1. Backend | Modeller, admin paneli, oturum/soru/cevap API'si, puanlama, skor tablosu, testler | 2 hafta |
| 2. Frontend | 4 ekran, süre çubuğu, API entegrasyonu, canlı tema ve animasyonlar | 2 hafta |
| 3. Test ve yayın | Uçtan uca test, güvenlik kontrolü, staging → production, izleme | 1 hafta |
| 4. Mobil | Teknoloji kararı, mobil istemci, mağaza yayını | 4–6 hafta |

**Test stratejisi**

- **Backend:** pytest ile servis katmanı (puan, süre aşımı, çift cevap) ve API testleri; hedef kapsama en az %80.
- **Frontend:** Vitest ile store ve bileşen testleri; Playwright ile "kategori seç → 20 soru → isim → skor tablosu" uçtan uca akışı.
- **Yük testi:** Eşzamanlı 200 oturum simülasyonu (ör. Locust).

**Dağıtım ve izleme:** GitHub Actions (veya GitLab CI) ile test ve imaj oluşturma; Docker ile dağıtım; Sentry ile hata izleme; PostgreSQL günlük yedeği.

**Cevaplanması gereken sorular**

- Skor tablosu kategori bazlı mı, genel mi, yoksa ikisi birden mi olsun?
- Soru içerikleri kim tarafından ve hangi kaynaklardan hazırlanacak?
- Mobil uygulama teknolojisi ve hedef platformlar (iOS, Android veya ikisi) neler?
- Uygulama için alan adı ve barındırma sağlayıcısı belirlendi mi?

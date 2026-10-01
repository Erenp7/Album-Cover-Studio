# PDA-226 – Album Cover Studio
**SE 226 Spring 2025-2026 | İzmir University of Economics**

---

## Kurulum

### 1. Gereksinimler
```
Python 3.10+
pip install -r requirements.txt
```

### 2. API Anahtarlarını Ayarla
`app.py` dosyasını aç ve şu satırları güncelle:
```python
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"   # aistudio.google.com/apikey
LASTFM_API_KEY = "YOUR_LASTFM_API_KEY_HERE"   # last.fm/api/account/create
```

### 3. Uygulamayı Çalıştır
```
python app.py
```

---

## Kullanım
1. Metin alanına ruh halinizi veya bir günlük girişi yazın.
2. Müzik türünü, dönemi ve parça sayısını seçin.
3. **GENERATE ALBUM** butonuna tıklayın.
4. Uygulama sırasıyla şunları yapar:
   - Gemini'ye albüm metadata'sını ürettirir
   - Last.fm'den gerçek şarkıları çeker
   - Pollinations.ai ile kapak görseli oluşturur
5. Her parça satırındaki **LISTEN** butonu şarkının Last.fm sayfasını açar.
6. **SAVE ALBUM** ile JSON + PNG olarak kaydedin.

---

## Karşılanan Gereksinimler
| # | Gereksinim | Durum |
|---|-----------|-------|
| R1 | Last.fm `tag.gettoptracks` API entegrasyonu | ✅ |
| R2 | Tkinter + ttk widget'ları | ✅ |
| R3 | Çok satırlı metin alanı, dropdown, spinbox, default değerler | ✅ |
| R4 | Gemini JSON çıktısı ve markdown fence temizleme | ✅ |
| R5 | Tekrar eden parçaların filtrelenmesi, doğru parça sayısı | ✅ |
| R6 | Pollinations.ai ile kapak görseli oluşturma | ✅ |
| R7 | Spotify tarzı layout, LISTEN butonları | ✅ |
| R8 | JSON + PNG kaydetme | ✅ |
| R9 | Background threading, durum etiketi | ✅ |

---

## Proje Yapısı
```
pda226/
├── app.py            # Ana uygulama (tüm kod tek dosyada)
├── requirements.txt  # Python bağımlılıkları
└── README.md         # Bu dosya
```

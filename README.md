# 🎓 Yapay Zeka Destekli Eğitim Asistanı

Bu proje, Google Gemini AI kullanarak öğrencilere interaktif konu anlatımı ve test çözümü sunan bir eğitim platformudur. Streamlit arayüzü ile kullanıcı dostu bir deneyim sağlar.

## 🚀 Özellikler

- 📚 Farklı dersler ve konularda kişiselleştirilmiş konu anlatımı
- 📝 Dinamik test oluşturma (1-10 arası rastgele soru)
- ✅ Anlık sınav değerlendirme ve geri bildirim
- 📊 Performans takibi ve skor hesaplama
- 🎯 Sınıf seviyesine uygun içerik

## 🛠️ Kurulum

1. Repository'yi klonlayın:

```
bash
git clone https://github.com/kullaniciadi/proje-adi.git
cd proje-adi
 ```
2. Gerekli paketleri yükleyin:

```
bash
pip install -r requirements.txt
```


3. Google API anahtarınızı ayarlayın:
   - [Google AI Studio](https://makersuite.google.com/app/apikey)'dan API anahtarı alın
   - `.env` dosyası oluşturun ve API anahtarınızı ekleyin:

```
env
GOOGLE_API_KEY=sizin_api_anahtariniz
```

4. Uygulamayı çalıştırın:

```
bash
streamlit run app.py
```


## 📋 Kullanım

1. Ders seçin (Matematik, Fizik, Kimya, Biyoloji)
2. Sınıf seviyesini belirleyin
3. Konu başlığını girin
4. "Konu Anlat" butonuna tıklayın
5. Konu anlatımını okuyun
6. Oluşturulan test sorularını çözün
7. "Cevapları Kontrol Et" ile performansınızı görün

## 🔧 Gereksinimler

- Python 3.8+
- Streamlit
- Google Generative AI
- python-dotenv
- [Diğer gereksinimler için requirements.txt dosyasına bakın]

## 📁 Proje Yapısı

proje/
│
├── app.py # Ana uygulama dosyası
├── requirements.txt # Gerekli paketler
├── .env # Çevresel değişkenler
├── .gitignore # Git tarafından göz ardı edilecek dosyalar
└── README.md # Proje dokümantasyonu


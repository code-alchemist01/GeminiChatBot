from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import google.generativeai as genai
from PIL import Image
import random
import re

# API yapılandırması
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Model yüklemeleri
chat_model = genai.GenerativeModel("gemini-1.5-flash")
vision_model = genai.GenerativeModel("gemini-1.5-flash")
qa_model = genai.GenerativeModel("gemini-1.5-flash")

# Chat geçmişi başlatma
chat = chat_model.start_chat(history=[])

# Yardımcı fonksiyonlar
def get_chat_response(input):
    response = chat.send_message(input, stream=True)
    return response

def get_vision_response(input, image):
    if input != "":
        response = vision_model.generate_content([input, image])
    else:
        response = vision_model.generate_content(image)
    return response.text

def get_qa_response(prompt):
    response = qa_model.generate_content(prompt)
    return response.text

def get_education_response(subject, topic, grade):
    # Konuya özgü anahtar kelimeleri belirleme
    keywords = f"{subject} {topic}".lower()
    
    # Prompt şablonu
    prompt = f"""Sen deneyimli bir {subject} öğretmenisin. {grade}. sınıf düzeyinde {topic} konusunu 
    öğrencilerin anlayabileceği şekilde, güncel örnekler ve interaktif bir yaklaşımla anlatmalısın.
    
    Lütfen şu başlıklar altında detaylı bir anlatım yap:
    1. Konunun günlük hayattaki önemi ve kullanım alanları
    2. Temel kavramlar ve tanımlar
    3. Detaylı konu anlatımı (görsellerle desteklenmiş gibi düşün)
    4. Güncel teknoloji ve bilimsel gelişmelerle bağlantılar
    5. İlginç bilgiler ve dikkat çekici örnekler
    6. Sık yapılan hatalar ve çözüm önerileri
    7. Konuyu pekiştirici sorular ve problemler
    8. İleri düzey uygulamalar ve projeler

    Anlatımdan sonra, konuyla ilgili 5 adet test sorusu hazırla.
    Soruları ve cevapları aşağıdaki formatta ver:

    TEST BAŞLANGIÇ
    SORU 1:
    [Soru metni]
    
    A) [Seçenek]
    B) [Seçenek]
    C) [Seçenek]
    D) [Seçenek]

    SORU 2:
    [Soru metni]
    
    A) [Seçenek]
    B) [Seçenek]
    C) [Seçenek]
    D) [Seçenek]

    [Diğer sorular...]

    CEVAP ANAHTARI:
    1. [Doğru cevap harfi]
    2. [Doğru cevap harfi]
    3. [Doğru cevap harfi]
    4. [Doğru cevap harfi]
    5. [Doğru cevap harfi]
    TEST BİTİŞ
    """
    
    try:
        # AI modelinden yanıt al
        response = qa_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )
        
        # Yanıtı işle
        full_response = response.text
        
        # Test bölümünü ayır
        if "TEST BAŞLANGIÇ" in full_response:
            parts = full_response.split("TEST BAŞLANGIÇ")
            main_content = parts[0].strip()
            
            test_part = parts[1]
            if "CEVAP ANAHTARI:" in test_part:
                questions = test_part.split("CEVAP ANAHTARI:")[0].strip()
                answers = test_part.split("CEVAP ANAHTARI:")[1].split("TEST BİTİŞ")[0].strip()
                
                # Session state'e kaydet
                st.session_state['test_questions'] = questions
                st.session_state['test_answers'] = answers
                st.session_state['answers_checked'] = False
                st.session_state['user_answers'] = [None] * 5
                
                return main_content
            
        return full_response
        
    except Exception as e:
        return f"Üzgünüm, bir hata oluştu: {str(e)}"

def generate_new_question(subject, topic, grade):
    """
    Belirli bir ders, konu ve sınıf seviyesi için yeni bir test sorusu oluşturur.
    """
    try:
        # Konu özelinde anahtar kelimeleri belirle
        subject_keywords = {
            "Matematik": ["hesaplama", "problem çözme", "matematiksel düşünme"],
            "Türkçe": ["anlama", "yorumlama", "dil bilgisi"],
            "Fen Bilimleri": ["bilimsel düşünme", "gözlem", "analiz"],
            # Diğer dersler için benzer anahtar kelimeler...
        }

        keywords = subject_keywords.get(subject, ["temel kavramlar", "uygulama", "analiz"])
        
        prompt = f"""
        {grade} seviyesinde {subject} dersinin {topic} konusuyla ilgili bir test sorusu oluştur.
        
        Konu anahtar kelimeleri: {', '.join(keywords)}
        
        Lütfen şu kurallara uy:
        1. Soru {grade} seviyesine uygun olmalı
        2. {topic} konusuyla doğrudan ilgili olmalı
        3. Şıklar mantıklı ve ayırt edici olmalı
        4. Yalnızca bir doğru cevap olmalı
        5. Her şık benzersiz olmalı
        
        Yanıtı tam olarak bu formatta ver:
        SORU: [soru metni]
        A) [seçenek]
        B) [seçenek]
        C) [seçenek]
        D) [seçenek]
        CEVAP: [doğru şıkkın harfi]
        """

        response = qa_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        # Yanıtı işle
        response_text = response.text.strip()
        
        # Soru ve cevabı ayır
        if "SORU:" in response_text and "CEVAP:" in response_text:
            # Metni parçalara ayır
            parts = response_text.split("CEVAP:")
            question_part = parts[0].replace("SORU:", "").strip()
            answer = parts[1].strip()[0].upper()  # Sadece ilk harfi al
            
            return {
                "question": question_part,
                "answer": answer,
                "success": True
            }
        else:
            return {
                "success": False,
                "error": "Soru formatı geçersiz"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Ders ve konu yapılandırması
grade_subjects = {
    "1. Sınıf": {
        "Matematik": ["Doğal Sayılar", "Ritmik Sayma", "Toplama İşlemi", "Çıkarma İşlemi", "Geometrik Cisimler", "Uzamsal İlişkiler", "Ölçme", "Veri Analizi", "Örüntüler", "Problem Çözme", "Sayı Örntüleri", "Geometrik Şekiller"],
        "Türkçe": ["Okuma Yazma", "Ses Bilgisi", "Hece Bilgisi", "Kelime Bilgisi", "Cümle Bilgisi", "Metin Türleri", "Dinleme", "Konuşma", "Yazma", "Görsel Okuma", "Noktalama", "Yazım Kuralları"],
        "Hayat Bilgisi": ["Ben ve Okulum", "Ailem", "Sağlıklı Hayat", "Güvenli Hayat", "Doğa ve Çevre", "Ülkemi Seviyorum", "Değerlerimiz", "Teknoloji", "Üretim ve Tüketim", "Meslekler", "Bayramlar", "Doğal Afetler"],
        "İngilizce": ["Selamlaşma", "Renkler", "Sayılar", "Hayvanlar", "Meyveler", "Aile", "Vücudumuz", "Oyuncaklar", "Duygular", "Hava Durumu", "Yiyecekler", "Giyecekler"]
    },
    "2. Sınıf": {
        "Matematik": ["Sayılar ve İşlemler", "Çarpma İşlemi", "Bölme İşlemi", "Kesirler", "Geometri", "Ölçme Birimleri", "Zaman Ölçüleri", "Para Hesaplamaları", "Veri İşleme", "Problemler", "Örüntü ve Süsleme", "Simetri"],
        "Türkçe": ["Okuma Stratejileri", "Anlama", "Kelime Hazinesi", "Dil Bilgisi", "Yazı Yazma", "Metin Yazma", "Şiir", "Hikaye", "Masal", "İletişim", "Medya Okuryazarlığı", "Yaratıcı Yazma"],
        "Hayat Bilgisi": ["Okul Kuralları", "De��erlerimiz", "Sağlıklı Beslenme", "Trafik", "Doğa ve İnsan", "Canlılar", "Milli Bayramlar", "Tasarruf", "İletişim", "Güvenlik", "Bilinçli Tüketim", "Çevre Koruma"],
        "İngilizce": ["Okul Eşyaları", "Taşıtlar", "Meslekler", "Spor", "Hobiler", "Ev Eşyaları", "Günlük Rutinler", "Kıyafetler", "Hayvanlar", "Yiyecekler", "Mevsimler", "Duygular"]
    },
    "3. Sınıf": {
        "Matematik": ["Doğal Sayılarla İşlemler", "Kesirlerle İşlemler", "Geometrik Şekiller", "Uzunluk Ölçme", "Çevre Hesaplama", "Alan Hesaplama", "Zaman Ölçme", "Tartma", "Sıvı Ölçme", "Veri Toplama", "Grafik Oluşturma", "Problem Çözme"],
        "Türkçe": ["Okuma Becerileri", "Metin Analizi", "Söz Varlığı", "Cümle Yapıları", "Paragraf Yazma", "Kompozisyon", "Sunum Yapma", "Tartışma", "Araştırma", "Rapor Yazma", "Dijital Okuma", "Eleştirel Düşünme"],
        "Fen Bilimleri": ["Canlılar Dünyası", "Besinler", "Maddenin Özellikleri", "Kuvvet ve Hareket", "Işık ve Ses", "Elektrik", "Gezegenimiz", "Hava Olayları", "Çevre Kirliliği", "Geri Dönüşüm", "Sağlık", "Bilim ve Teknoloji"],
        "Hayat Bilgisi": ["Toplum Hayatı", "Doğal Çevre", "Milli Kültür", "Sağlıklı Yaşam", "Güvenli Yaşam", "Üretim ve Tüketim", "Bilim ve Teknoloji", "İletişim", "Vatandaşlık", "Kaynaklar", "Doğal Afetler", "Çevre Bilinci"],
        "İngilizce": ["Günlük Rutinler", "Okul Hayatı", "Hobiler", "Şehir Yaşamı", "Yönler", "Alışveriş", "Sağlık", "Tatil", "Hava Durumu", "Spor", "Yemek Tarifleri", "Teknoloji"]
    },
    "4. Sınıf": {
        "Matematik": ["Büyük Sayılar", "Kesirler", "Ondalık Gösterim", "Açılar", "Üçgenler", "Dörtgenler", "Uzunluk Ölçüleri", "Alan Ölçme", "Zaman Ölçüleri", "Veri Toplama", "Grafik", "Simetri"],
        "Türkçe": ["Okuma Teknikleri", "Anlama", "Kelime Bilgisi", "Dil Bilgisi", "Yazım Kuralları", "Noktalama", "Paragraf", "Metin Türleri", "Şiir", "Hikaye", "Kompozisyon", "Sunum"],
        "Fen Bilimleri": ["Vücudumuz", "Kuvvet ve Hareket", "Maddeyi Tanıyalım", "Işık ve Ses", "Gezegenimiz", "Mikroskobik Canlılar", "Basit Makineler", "Elektrik", "Çevre Kirliliği", "Canlılar Dünyası", "Besinler", "Enerji"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar ve Yönetim", "Bilim ve Teknoloji", "Üretim ve Tüketim", "Küresel Bağlantılar", "Çevre", "Doğal Afetler", "Demokrasi", "İnsan Hakları", "Milli Kltür", "Vatandaşlık"],
        "İngilizce": ["Kişisel Bilgiler", "Aile ve Arkadaşlar", "Gnlük Yaşam", "Boş Zaman", "Şehir ve Ulaşım", "Tatil", "Alışveriş", "Yemek ve İçecek", "Sağlık", "Doğa ve Çevre", "Teknoloji", "Kültür"]
    },
    "5. Sınıf": {
        "Matematik": ["Doğal Sayılar", "Kesirler", "Ondalık G��sterim", "Yüzdeler", "Temel Geometri", "Üçgenler", "Dörtgenler", "Veri İşleme", "Uzunluk Ölçme", "Alan Ölçme", "Zaman Ölçme", "Problem Çözme"],
        "Türkçe": ["Okuma", "Yazma", "Dinleme", "Konuşma", "Dil Bilgisi", "Kelime Bilgisi", "Cümle Bilgisi", "Metin Bilgisi", "Anlama", "Anlatım", "Yazım Kuralları", "Noktalama"],
        "Fen Bilimleri": ["Canlılar Dünyası", "İnsan ve Çevre", "Kuvvetin Ölçülmesi", "Madde ve Değişim", "Işık ve Ses", "Elektrik", "Yerkabuğu", "Dünya ve Evren", "Canlılar ve Yaşam", "Fiziksel Olaylar", "Madde", "Enerji"],
        "Sosyal Bilgiler": ["Birey ve Toplum", "Kültür ve Miras", "İnsanlar ve Yerler", "Bilim ve Teknoloji", "Üretim ve Tüketim", "Etkin Vatandaşlık", "Küresel Bağlantılar", "Coğrafya", "Tarih", "Ekonomi", "Yönetim", "Sosyal Bilimler"],
        "İngilizce": ["Greeting", "My Town", "Games and Hobbies", "My Daily Routine", "Health", "Movies", "Party Time", "Fitness", "Animal Shelter", "Environment", "Planets", "Democracy"]
    },
    "6. Sınıf": {
        "Matematik": ["Tam Sayılar", "Kesirlerle İşlemler", "Ondalık Gösterim", "Oran ve Orantı", "Cebirsel İfadeler", "Geometrik Şekiller", "Alan Ölçme", "Çember", "Veri Analizi", "Prizmalar", "Dönüşüm Geometrisi", "Problem Çözme"],
        "Türkçe": ["Okuma Stratejileri", "Yazma Teknikleri", "Söz Sanatları", "Paragraf", "Cümle Türleri", "Sözcük Türleri", "Anlatım Bozuklukları", "Metin Türleri", "Dil Bilgisi", "Yazım Kuralları", "Noktalama", "Anlama"],
        "Fen Bilimleri": ["Vücudumuzdaki Sistemler", "Kuvvet ve Hareket", "Madde ve Isı", "Ses ve Özellikleri", "Işık ve Yayılması", "Elektrik", "Dünyamız", "Güneş Sistemi", "Canlılar ve Yaşam", "Madde ve Değişim", "Fiziksel Olaylar", "Enerji"],
        "Sosyal Bilgiler": ["Yeryüzü", "İlk Uygarlıklar", "İpek Yolu", "Orta Asya", "İslamiyet", "Türk Tarihi", "Coğrafi Keşifler", "Osmanlı Devleti", "Demokrasi", "Ekonomi", "Sosyal Yaşam", "Bilim ve Teknoloji"],
        "İngilizce": ["After School", "Yummy Breakfast", "A Day in My City", "Weather and Emotions", "At the Fair", "Occupations", "Detectives at Work", "Saving the Planet", "Democracy", "Festivals", "Bookworms", "Saving the Planet"]
    },
    "7. Sınıf": {
        "Matematik": ["Tam Sayılarla İşlemler", "Rasyonel Sayılar", "Oran-Orantı", "Yüzdeler", "Eşitlik ve Denklem", "Doğrusal Denklemler", "Çember ve Daire", "Veri Analizi", "Dönşüm Geometrisi", "Cisimlerin Yüzey Alanı", "Olasılık", "Cebirsel İfadeler"],
        "Türkçe": ["Fiilimsiler", "Cümle Türleri", "Anlatım Bozuklukları", "Söz Sanatları", "Metin Bilgisi", "Yazım Kuralları", "Noktalama", "Paragraf", "Anlatım Biçimleri", "Düşünceyi Geliştirme", "Metin Türleri", "Dil Bilgisi"],
        "Fen Bilimleri": ["Hücre ve Bölünmeler", "Kuvvet ve Enerji", "Maddenin Yapısı", "Saf Maddeler", "Karışımlar", "Işık", "Elektrik", "Güneş Sistemi", "Dünya ve Ay", "Canlılarda Üreme", "Enerji Dnüşümleri", "Küresel Isınma"],
        "Sosyal Bilgiler": ["İletişim ve İnsan İlişkileri", "Türk Tarihi", "Nüfus ve Yerleşme", "Ekonomi ve Sosyal Hayat", "Zaman İçinde Bilim", "Yaşayan Demokrasi", "Ülkeler Arası Köprüler", "Osmanlı Kültürü", "Avrupa ve Osmanlı", "Ekonomik Gelişmeler", "Coğrafi Keşifler", "Kültür ve Miras"],
        "İngilizce": ["Appearance and Personality", "Sports", "Biographies", "Wild Animals", "Television", "Celebrations", "Dreams", "Public Buildings", "Environment", "Planets", "Superstitions", "Natural Forces"]
    },
    "8. Sınıf": {
        "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık", "Cebirsel İfadeler", "Denklemler", "Eşitsizlikler", "Üçgenler", "Dönüşüm Geometrisi", "Geometrik Cisimler", "Örüntüler"],
        "Türkçe": ["Fiilimsiler", "Cümle Türleri", "Söz Sanatları", "Anlatım Bozuklukları", "Yazım Kuralları", "Noktalama", "Paragraf", "Metin Türleri", "Anlatım Biçimleri", "Düşünceyi Geliştirme", "Dil Bilgisi", "Yazılı Anlatım"],
        "Fen Bilimleri": ["DNA ve Genetik", "Basınç", "Periyodik Sistem", "Maddenin Yapısı", "Kimyasal Tepkimeler", "Asitler ve Bazlar", "Elektrik Yükleri", "Mevsimlerin Oluşumu", "Enerji Dönüşümleri", "Besin Zinciri", "Adaptasyon", "Sürdürülebilir Yaşam"],
        "İnkılap Tarihi": ["Bir Kahraman Doğuyor", "Milli Uyanış", "Kurtuluş Savaşı", "ağdaşlaşan Türkiye", "Atatürk İlkeleri", "Demokratikleme", "Atatürk Dönemi", "Türk Dış Politikası", "Cumhuriyet Dönemi", "Ekonomi Politikalar", "Sosyal Politikalar", "Kültür ve Sanat"],
        "İngilizce": ["Friendship", "Teen Life", "Cooking", "Communication", "The Internet", "Adventures", "Tourism", "Chores", "Science", "Natural Forces", "History", "Democracy"]
    },
    "9. Sınıf": {
        "Matematik": ["Mantık", "Kümeler", "Denklemler", "Üçgenler", "Veri Analizi", "Fonksiyonlar", "Polinomlar", "Olasılık", "Geometrik Cisimler", "Trigonometri", "Permütasyon", "Kombinasyon"],
        "Türk Dili ve Edebiyatı": ["Giriş", "Hikaye", "Şiir", "Masal", "Destan", "Roman", "Tiyatro", "Dil Bilgisi", "Edebiyat Akımları", "Edebi Sanatlar", "Dünya Edebiyatı", "Metin Tahlili"],
        "Fizik": ["Fizik Bilimine Giriş", "Madde ve Özellikleri", "Hareket", "Kuvvet", "Enerji", "Isı ve Sıcaklık", "Elektrostatik", "Basınç", "Dalgalar", "Optik", "Manyetizma", "Modern Fizik"],
        "Kimya": ["Kimya Bilimi", "Atom", "Periyodik Sistem", "Kimyasal Türler", "Mol Kavramı", "Karışımlar", "Asit-Baz", "Maddenin Halleri", "Çözeltiler", "Kimyasal Tepkimeler", "Gazlar", "Kimya ve Teknoloji"],
        "Biyoloji": ["Canlılar", "Hücre", "Canlı Çeşitliliği", "Ekosistem", "Güncel Çevre Sorunları", "Biyolojik Çeşitlilik", "Hücre Bölünmesi", "Kalıtım", "Evrim", "Biyoteknoloji", "Canlı Sistemleri", "Metabolizma"],
        "Tarih": ["Tarih Bilimi", "İlk Uygarlıklar", "İlk Türk Devletleri", "İslamiyet", "Türk-slam Devletleri", "Türkiye Tarihi", "Osmanlı Kuruluş", "Osmanlı Yükselme", "Osmanlı Kültür", "Dünya Tarihi", "Avrupa Tarihi", "Orta Çağ"],
        "Coğrafya": ["Doğal Sistemler", "Dünya", "Harita Bilgisi", "İklim", "Yerşekilleri", "Nüfus", "Yerleşme", "Ekonomik Faaliyetler", "Çevre ve Toplum", "Bölgeler", "Afetler", "Küresel Ortam"],
        "İngilizce": ["Personal Life", "Plans", "Human in Nature", "Coming Soon", "Inspirational People", "Bridging Cultures", "World Heritage", "Emergency and Health", "Invitations and Celebrations", "Television", "Sports", "Technology"]
    },
    "10. Sınıf": {
        "Matematik": ["Fonksiyonlar", "Polinomlar", "İkinci Dereceden Denklemler", "Trigonometri", "Geometri", "Analitik Geometri", "Çember", "Daire", "Katı Cisimler", "Olasılık", "İstatistik", "Logaritma"],
        "Türk Dili ve Edebiyatı": ["Divan Edebiyatı", "Halk Edebiyatı", "Tanzimat Edebiyatı", "Servet-i Fünun", "Milli Edebiyat", "Cumhuriyet Dönemi", "Roman", "Hikaye", "Şiir", "Tiyatro", "Deneme", "Makale"],
        "Fizik": ["Elektrik", "Manyetizma", "Basınç", "Kaldırma Kuvveti", "Dalgalar", "Optik", "Hareket", "Dinamik", "İş ve Enerji", "Isı ve Sıcaklık", "Gazlar", "Modern Fizik"],
        "Kimya": ["Karışımlar", "Asitler ve Bazlar", "Kimyasal Tepkimeler", "Gazlar", "Sıvılar", "Katılar", "Çözeltiler", "Kimyasal Bağlar", "Organik Kimya", "Karbon Kimyası", "Endüstriyel Kimya", "Analitik Kimya"],
        "Biyoloji": ["Hücre Bölünmesi", "Kalıtım", "Ekosistem", "Güncel Çevre Sorunları", "Solunum", "Dolaşım", "Sindirim", "Boşaltım", "Sinir Sistemi", "Endokrin Sistem", "Duyu Organları", "Üreme"],
        "Tarih": ["Osmanlı Duraklama", "Osmanlı Gerileme", "Osmanlı Dağılma", "Avrupa Tarihi", "Fransız İhtilali", "Sanayi Devrimi", "I. Dünya Savaşı", "Kurtuluş Savaşı", "İnkılaplar", "Atatürk Dnemi", "II. Dünya Savaşı", "Soğuk Savaş"],
        "Coğrafya": ["İklim", "Bitki Örtüsü", "Toprak", "Su", "Nüfus", "Göç", "Yerleşme", "Ekonomik Faaliyetler", "Ulaşım", "Ticaret", "Turizm", "Doğal Kaynaklar"],
        "İngilizce": ["School Life", "Plans and Dreams", "Legendary Figures", "Traditional Crafts", "Travel", "Helpful Tips", "Food and Festivals", "Digital Era", "Modern Heroes", "Shopping", "Psychology", "Values"]
    },
    "11. Sınıf": {
        "Matematik": ["Türev", "İntegral", "Limit", "Trigonometri", "Logaritma", "Diziler", "Seriler", "Karmaşık Sayılar", "Olasılık", "İstatistik", "Analitik Geometri", "Geometri"],
        "Türk Dili ve Edebiyatı": ["Cumhuriyet Dönemi", "Modern Edebiyat", "Dünya Edebiyatı", "Roman Tahlili", "Şiir Tahlili", "Edebi Akımlar", "Metin Yorumlama", "Dil Bilgisi", "Anlatım Teknikleri", "Yazım ve Noktalama", "Söz Sanatları", "Edebi Türler"],
        "Fizik": ["Kuvvet ve Hareket", "Elektrik ve Manyetizma", "Modern Fizik", "Dalgalar", "Optik", "Kuantum", "Atom Fiziği", "Nükleer Fizik", "Radyoaktivite", "Görelilik", "Yarı İletkenler", "Astronomi"],
        "Kimya": ["Kimyasal Tepkimeler", "Gaz Yasaları", "Çözeltiler", "Kimyasal Denge", "Asit-Baz Dengesi", "Çözünürlük", "Elektrokimya", "Organik Kimya", "Polimer", "Endüstriyel Kimya", "Biyokimya", "Analitik Kimya"],
        "Biyoloji": ["Hücre Bölünmesi", "Kalıtım", "Ekosistem", "Sinir Sistemi", "Endokrin Sistem", "Duyu Organları", "Destek ve Hareket", "Sindirim", "Dolaşım", "Solunum", "Boşaltım", "Rreme"],
        "Tarih": ["20. Yüzyıl Başları", "I. Dünya Savaşı", "Kurtuluş Savaşı", "Türkiye Cumhuriyeti", "Atatürk Dönemi", "İnönü Dönemi", "Demokrat Parti", "1960 Sonrası", "Dünya Savaşları", "Soğuk Savaş", "Yakın Tarih", "Günümüz Dünyası"],
        "Coğrafya": ["Doğal Sistemler", "Ekosistem", "Nüfus", "Yerleşme", "Ekonomik Faaliyetler", "Ulaşım", "Ticaret", "Turizm", "Doğal Kaynaklar", "Çevre Sorunları", "Afetler", "Küresel Sorunlar"],
        "İngilizce": ["Future Jobs", "Hobbies", "Hard Times", "What A Life", "News Stories", "Favours", "Social Media", "Language Learning", "Sports", "Brain Power", "World Heritage", "Modern Life"]
    },
    "12. Sınıf": {
        "Matematik": ["Limit ve Süreklilik", "Türev", "İntegral", "Diziler", "Karmaşık Sayılar", "Olasılık", "İstatistik", "Geometri", "Analitik Geometri", "Trigonometri", "Logaritma", "Fonksiyonlar"],
        "Türk Dili ve Edebiyatı": ["Cumhuriyet Sonrası", "Çağdaş Türk Edebiyatı", "Modern Dünya Edebiyatı", "Edebi Eleştiri", "Metin Çözümleme", "Dil ve Anlatım", "Kompozisyon", "Yazım ve Noktalama", "Söz Sanatları", "Edebi Akımlar", "Roman İnceleme", "Şiir Tahlili"],
        "Fizik": ["Çembersel Hareket", "Basit Harmonik Hareket", "Dalga Mekaniği", "Atom Fiziği", "Nükleer Fizik", "Modern Fizik", "Kuantum Fiziği", "Görelilik", "Yarı İletkenler", "Fotoelektrik", "Compton Olayı", "Radyoaktivite"],
        "Kimya": ["Kimyasal Tepkimeler", "Kimyasal Denge", "Asit-Baz Dengesi", "Çözünürlük", "Elektrokimya", "Organik Kimya", "Polimer", "Endüstriyel Kimya", "Biyokimya", "İlaç Kimyası", "Nanoteknoloji", "Yeşil Kimya"],
        "Biyoloji": ["Hücre Bölünmesi", "Kalıtım", "Biyoteknoloji", "Canlılarda Enerji", "Bitki Biyolojisi", "Hayvan Biyolojisi", "Davranış", "Topluluk Ekolojisi", "Popülasyon", "Evrim", "Biyolojik Çeşitlilik", "Güncel Biyoloji"],
        "Tarih": ["Türkiye Cumhuriyeti", "Atatürk İlkeleri", "İnkılaplar", "Çağdaşlaşma", "Demokrasi Tarihi", "Türk Dış Politikası", "Soğuk Savaş", "Yakın Tarih", "Küreselleşme", "Uluslararası İlişkiler", "Güncel Sorunlar", "21. Yüzyıl"],
        "Coğrafya": ["Doğal Sistemler", "Beşeri Sistemler", "Mekansal Sentez", "Küresel Ortam", "Çevre ve Toplum", "Bölgeler", "Türkiye'nin Konumu", "Nüfus Politikaları", "Ekonomik Faaliyetler", "Uluslararası Ulaşım", "Doğal Kaynaklar", "Sürdürülebilirlik"],
        "İngilizce": ["Psychology", "Inspirational People", "Modern Life", "International Relations", "Career Plans", "Environmental Issues", "Technology", "Art and Culture", "Science and Innovation", "Global Issues", "Media Literacy", "Future Trends"]
    }
}

# Streamlit sayfa yapılandırması
st.set_page_config(
    page_title="EduApp Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS stilleri
st.markdown("""
    <style>
    /* Tüm metinler için genel stil */
    body, p, span, label, h1, h2, h3, .streamlit-expanderHeader, 
    .stMarkdown, .stText, .card h2, .card p {
        color: #ffffff !important;
    }
    
    /* Başlık stilleri */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    h2 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }
    
    /* Kart stilleri */
    .card {
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Form elemanları */
    .stTextInput label, .stSelectbox label, .stRadio label {
        font-size: 1rem !important;
        font-weight: 500 !important;
    }
    
    /* Tab stilleri */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500 !important;
    }
    
    /* Buton stilleri */
    .stButton button {
        font-weight: 500 !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .stButton button:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Yardımcı metinler */
    .help-text {
        opacity: 0.8;
    }
    
    /* Konu anlatım kartı */
    .education-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Seçim kutuları */
    .selection-container {
        background: rgba(255,255,255,0.05);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    
    /* Test soruları kartı */
    .test-card {
        background: rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .question-box {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
    
    .option-box {
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .option-box:hover {
        background: rgba(255,255,255,0.1);
        transform: translateX(10px);
    }
    
    /* Sonuç kartı */
    .result-card {
        background: linear-gradient(145deg, rgba(76,175,80,0.1) 0%, rgba(76,175,80,0.05) 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(76,175,80,0.2);
    }
    
    /* Progress bar */
    .progress-container {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Animasyonlu butonlar */
    .action-button {
        background: linear-gradient(145deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(76,175,80,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Ana başlık
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>📚 EduApp Chatbot</h1>", unsafe_allow_html=True)

# Session state başlatma
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'qa_history' not in st.session_state:  # QA geçmişi için yeni session state
    st.session_state['qa_history'] = []
if 'education_content' not in st.session_state:
    st.session_state['education_content'] = None
if 'test_question' not in st.session_state:
    st.session_state['test_question'] = None
if 'test_answer' not in st.session_state:
    st.session_state['test_answer'] = None
if 'user_answer' not in st.session_state:
    st.session_state['user_answer'] = None
if 'answer_checked' not in st.session_state:
    st.session_state['answer_checked'] = False

# Sekmeleri oluşturma (daha modern görünüm)
tabs = st.tabs([
    "🖼️ Görsel Analiz",
    "❓ Soru-Cevap",
    "📖 Konu Anlatımı"
])

# Görsel analiz sekmesi
with tabs[0]:
    st.markdown("""
        <div class="card">
            <h2>🖼️ Görsel Analiz Modu</h2>
            <p>Yüklediğiniz görseller hakkında sorular sorun ve AI destekli analizler alın.</p>
        </div>
    """, unsafe_allow_html=True)
    
    vision_input = st.text_input(
        "Görsel hakkında sorunuz:",
        key="vision_input",
        help="Yüklediğiniz görsel hakkında sormak istediğiniz soruyu buraya yazın"
    )
    uploaded_file = st.file_uploader("Resim yükleyin", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen resim", use_column_width=True)
        
        if st.button("Analiz Et", key="vision_submit"):
            if vision_input:  # Boş input kontrolü
                response = get_vision_response(vision_input, image)
                # Sohbet geçmişine ekleme
                st.session_state['chat_history'].append({
                    'role': 'user',
                    'content': vision_input
                })
                st.session_state['chat_history'].append({
                    'role': 'assistant',
                    'content': response
                })
                st.subheader("Analiz Sonucu:")
                st.write(response)
            else:
                st.warning("Lütfen bir soru girin.")

    # Geçmişi silme butonu
    if st.button("Sohbet Geçmişini Temizle"):
        st.session_state['chat_history'] = []
        st.rerun()

    # Sohbet geçmişini görüntüleme
    if st.session_state['chat_history']:
        st.subheader("Sohbet Geçmişi")
        for message in st.session_state['chat_history']:
            role_label = "🙋‍♂️ Soru:" if message['role'] == 'user' else "🤖 Cevap:"
            st.write(f"{role_label} {message['content']}")

# Soru-Cevap sekmesi
with tabs[1]:
    st.markdown("""
        <div class="card">
            <h2>❓ Soru-Cevap Modu</h2>
            <p>Aklınızdaki her türlü soruyu sorun, AI asistanınız yanıtlasın.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Geçmişi silme butonu
    if st.button("Sohbet Geçmişini Temizle", key="clear_qa_history"):
        st.session_state['qa_history'] = []
        st.rerun()
    
    qa_input = st.text_input("Sorunuz:", key="qa_input")
    qa_submit = st.button("Sor", key="qa_submit")

    if qa_submit and qa_input:
        response = get_qa_response(qa_input)
        # Sohbet geçmişine ekleme
        st.session_state['qa_history'].append(("Soru", qa_input))
        st.session_state['qa_history'].append(("Cevap", response))
        st.subheader("Cevap:")
        st.write(response)

    # Sohbet geçmişini görüntüleme
    st.subheader("Sohbet Geçmişi")
    for role, text in st.session_state['qa_history']:
        st.write(f"{role}: {text}")

# Konu anlatım sekmesi
with tabs[2]:
    st.markdown("""
        <div class="education-card">
            <h2>📖 Konu Anlatım Modu</h2>
            <p>Seçtiğiniz ders ve konuda detaylı anlatım ve test soruları alın.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Seçim kutuları için container
    st.markdown('<div class="selection-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        grade = st.selectbox("📚 Sınıf Seçin:", list(grade_subjects.keys()))
    
    with col2:
        if grade in grade_subjects:
            subject = st.selectbox("📖 Ders Seçin:", list(grade_subjects[grade].keys()))
    
    if grade in grade_subjects and subject in grade_subjects[grade]:
        topic = st.selectbox("🎯 Konu Seçin:", grade_subjects[grade][subject])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Konu anlatımı oluşturma butonu
    if st.button("🚀 Konu Anlatımı Oluştur", key="generate_content"):
        with st.spinner("🎓 Konu anlatımı hazırlanıyor..."):
            content = get_education_response(subject, topic, grade)
            st.session_state['education_content'] = content
            
    # Oluşturulan içeriği göster
    if 'education_content' in st.session_state and st.session_state['education_content']:
        st.markdown('<div class="education-card">', unsafe_allow_html=True)
        st.write(st.session_state['education_content'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Test soruları bölümü
        if 'test_questions' in st.session_state and st.session_state['test_questions']:
            st.markdown('<div class="test-card">', unsafe_allow_html=True)
            st.markdown("<h3>📝 Test Soruları</h3>", unsafe_allow_html=True)
            
            # Soruları parçalara ayır
            questions_text = st.session_state['test_questions']
            
            # HTML ve code bloklarını temizle
            questions_text = re.sub(r'</?[^>]+/?>', '', questions_text)  # Tüm HTML etiketlerini kaldır
            questions_text = re.sub(r'</?\w+\s*/?>', '', questions_text)  # div, span gibi etiketleri kaldır
            questions_text = re.sub(r'\s*</div>\s*', '', questions_text)  # </div> etiketlerini özel olarak kaldır
            questions_text = re.sub(r'\s*<div[^>]*>\s*', '', questions_text)  # <div> etiketlerini özel olarak kaldır
            questions_text = re.sub(r'```[\s\S]*?```', '', questions_text)  # Code bloklarını kaldır

            # Gereksiz boşlukları temizle
            questions_text = re.sub(r'\n\s*\n', '\n\n', questions_text)  # Fazla boş satırları temizle
            questions_text = re.sub(r'[ \t]+', ' ', questions_text)  # Fazla boşlukları temizle
            questions_text = questions_text.strip()  # Baş ve sondaki boşlukları temizle

            st.session_state['test_questions'] = questions_text

            questions = questions_text.split('SORU')[1:]  # İlk boş elemanı atla
            
            # Her soru için ayrı kutu oluştur
            for i, question in enumerate(questions, 1):
                st.markdown(f"""
                    <div style="
                        background-color: rgba(255,255,255,0.05);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                        border: 1px solid rgba(255,255,255,0.1);
                    ">
                        <div style="
                            font-weight: bold;
                            margin-bottom: 15px;
                            font-size: 1.1em;
                            color: #4CAF50;
                        ">
                            Soru {i}:
                        </div>
                        <div style="margin-bottom: 20px;">
                            {question}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Şıklar için radio butonları
                st.radio(
                    "Cevabınız:",
                    ['A', 'B', 'C', 'D'],
                    key=f"answer_radio_{i-1}",
                    index=None,
                    horizontal=True
                )

            # Cevapları kontrol et butonu
            if st.button("✨ Cevapları Kontrol Et", key="check_answers"):
                st.session_state['answers_checked'] = True
                
                # Sonuçları göster
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                correct_answers = []
                answers_text = st.session_state['test_answers']
                
                # Doğru cevapları ayıkla
                for line in answers_text.split('\n'):
                    line = line.strip()
                    if line and any(str(num) in line for num in range(1, 6)):
                        answer = ''.join(c for c in line if c in 'ABCD')
                        if answer:
                            correct_answers.append(answer)
                
                # Kullanıcı cevaplarını kontrol et
                total_correct = 0
                for i in range(min(len(correct_answers), 5)):
                    user_answer = st.session_state.get(f"answer_radio_{i}")
                    correct_answer = correct_answers[i] if i < len(correct_answers) else None
                    
                    if user_answer and correct_answer and user_answer == correct_answer:
                        total_correct += 1
                        st.markdown(f"""
                            <div style="
                                color: #4CAF50;
                                padding: 10px;
                                border-radius: 5px;
                                margin: 5px 0;
                                background-color: rgba(76,175,80,0.1);
                            ">
                                ✅ Soru {i+1} Doğru! (Cevap: {correct_answer})
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div style="
                                color: #f44336;
                                padding: 10px;
                                border-radius: 5px;
                                margin: 5px 0;
                                background-color: rgba(244,67,54,0.1);
                            ">
                                ❌ Soru {i+1} Yanlış (Doğru cevap: {correct_answer})
                            </div>
                        """, unsafe_allow_html=True)
                
                # Toplam skor
                score_percentage = (total_correct / 5) * 100
                st.markdown(f"""
                    <div style="
                        text-align: center;
                        margin-top: 20px;
                        padding: 20px;
                        background: linear-gradient(145deg, rgba(76,175,80,0.1) 0%, rgba(76,175,80,0.05) 100%);
                        border-radius: 10px;
                    ">
                        <h3>📊 Sonuç</h3>
                        <div style="font-size: 2rem; margin: 10px 0;">%{score_percentage}</div>
                        <div>Toplam Doğru: {total_correct}/5</div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

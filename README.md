# Scopus Yayın Arama Uygulaması (Streamlit)

Elsevier Scopus veritabanında yazar, kurum ve tarih bazlı yayın araması yapan, Türkçe arayüze sahip interaktif bir web uygulamasıdır.

## Özellikler
- **Arama**: Yazar ID veya ORCID ile arama.
- **Filtreler**: Kurum ID, Konu Alanı, Yıl Aralığı ve Doküman Tipi filtreleri.
- **Güvenlik**: API Anahtarını arayüzden (oturum bazlı) veya Streamlit Secrets üzerinden girme imkanı.
- **Görselleştirme**: Yayınların aylık veya yıllık dağılımını gösteren grafikler.
- **Bağlantılar**: Makalelere doğrudan erişim için tıklanabilir DOI linkleri.
- **Modlar**:
  - **Canlı Mod**: API anahtarı ile gerçek Scopus verisini çeker.
  - **Mock Modu**: Anahtar girilmezse örnek veri ile çalışır.

## Yerel Kurulum

1. **Repoyu klonlayın:**
   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. **Gerekli paketleri yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Uygulamayı çalıştırın:**
   ```bash
   streamlit run app.py
   ```
   Tarayıcınızda `http://localhost:8501` adresinde açılacaktır.

## Streamlit Cloud Dağıtımı

1. Kodunuzu GitHub'a yükleyin.
2. [Streamlit Cloud](https://streamlit.io/cloud) hesabınıza giriş yapın.
3. **"New app"** butonuna tıklayın.
4. Reponuzu ve `app.py` dosyasını seçin.
5. **"Deploy"** butonuna basın.

### API Anahtarını Kaydetme (Opsiyonel)
Her seferinde anahtar girmemek için Streamlit Cloud ayarlarından ekleyebilirsiniz:

1. Uygulama paneline gidin -> **Settings** -> **Secrets**.
2. Aşağıdaki formatta anahtarınızı yapıştırın:
   ```toml
   SCOPUS_API_KEY = "buraya-scopus-api-anahtarinizi-yazin"
   ```
3. Kaydedin. Uygulama artık varsayılan olarak bu anahtarı kullanacaktır.

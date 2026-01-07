import streamlit as st
import pandas as pd
from scopus_service import ScopusService
import io

# Page Config
st.set_page_config(page_title="Scopus Yayın Arama", layout="wide")

# Title
st.title("🔎 Scopus Yayın Arama")

# Sidebar
with st.sidebar:
    st.header("Ayarlar")
    api_key = st.text_input("Scopus API Anahtarı", type="password", help="Boş bırakırsanız Mock Modu (test verisi) kullanılır.")

    st.markdown("---")
    st.caption("Emeği Geçenler")
    st.markdown("**Salih Keskin, 2026**")

# Main Interface
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Arama Kriterleri")
    with st.form("search_form"):
        # Search Type Selector
        search_type = st.radio("Arama Tipi", ["Yazar", "Kurum"], horizontal=True)

        identifier = None
        id_type = None
        af_id_input = None

        if search_type == "Yazar":
            author_id_type = st.selectbox("Yazar Kimliği", ["ORCID", "Yazar ID"])
            identifier = st.text_input(f"{author_id_type} Giriniz", placeholder="Örn: 0000-0000... veya 700421...")
            # Map selection to internal type
            id_type = "ORCID" if author_id_type == "ORCID" else "AU-ID"

            # Optional Affiliation filter for Author search
            with st.expander("Kurum Filtresi (Opsiyonel)"):
                af_id_input = st.text_input("Kurum ID (AF-ID)", value="", help="Yazarın sadece bu kurumdaki yayınlarını filtrele")
        else:
            # Affiliation Search
            af_id_input = st.text_input("Kurum ID (AF-ID)", value="60014930")
            identifier = None # No author identifier in this mode

        st.markdown("---")
        st.write("**Filtreler**")

        subj_area = st.text_input("Konu Alanı (SUBJAREA)", value="MEDI")
        doctype = st.text_input("Doküman Tipi (DOCTYPE)", value="ar")

        c1, c2 = st.columns(2)
        with c1:
            start_year = st.number_input("Başlangıç Yılı", value=2000, step=1)
        with c2:
            end_year = st.number_input("Bitiş Yılı", value=2027, step=1)

        limit = st.select_slider("Maksimum Sonuç Sayısı", options=[25, 50, 100, 1000], value=25)

        submit_button = st.form_submit_button("Yayınları Ara", type="primary")

# Logic
if submit_button:
    # Initialize Service
    service = ScopusService()

    # Prepare Filters
    filters = {
        "subj_area": subj_area,
        "start_year": start_year,
        "end_year": end_year,
        "doctype": doctype
    }

    # Handle Affiliation logic based on mode
    if search_type == "Kurum":
        # In Kurum mode, AF-ID is the main search, not a filter on an author
        # We pass it as 'main_af_id' to service or handle distinct logic
        filters["main_af_id"] = af_id_input
    elif af_id_input:
        # In Author mode, it's an extra filter
        filters["filter_af_id"] = af_id_input

    # Fetch Data
    with st.spinner("Scopus API üzerinden veri çekiliyor..."):
        # Pass id_type explicitly to helper
        result = service.get_publications(
            identifier=identifier,
            id_type=id_type,
            api_key=api_key,
            filters=filters,
            limit=limit
        )

    # Display Results in col2
    with col2:
        if "error" in result:
            st.error(f"Hata: {result['error']}")
            if "query_used" in result:
                st.code(result['query_used'], language="text")
        else:
            # Metadata & Stats
            total = result.get('total_results', 0)
            shown = result.get('shown_results', 0)
            source = result.get('source', 'Unknown')

            if total > shown:
                st.warning(f"⚠️ Toplam **{total}** sonuçtan **{shown}** adedi gösteriliyor. Daha fazlası için limiti artırın.")
            else:
                st.success(f"Toplam **{shown}** sonuç listelendi.")

            st.caption(f"Veri Kaynağı: {source}")

            if "query_used" in result:
                with st.expander("Sorguyu Görüntüle"):
                    st.code(result['query_used'], language="text")

            # Publications Table
            pubs = result.get('publications', [])

            # Tabs
            tab1, tab2 = st.tabs(["Sonuçlar", "Görselleştirme"])

            if pubs:
                df = pd.DataFrame(pubs)

                # --- Tab 1: Results ---
                with tab1:
                    # Construct DOI Link
                    if "doi" in df.columns:
                        df["doi_link"] = df["doi"].apply(lambda x: f"https://doi.org/{x}" if x and x != "N/A" else None)
                    else:
                        df["doi_link"] = None

                    # Rename columns for display
                    df_display = df.copy()
                    df_display = df_display.rename(columns={
                        "title": "Başlık",
                        "journal": "Dergi",
                        "year": "Yıl",
                        "times_cited": "Atıf",
                        "doctype": "Tip",
                        "doi": "DOI",
                        "scopus_id": "Scopus ID",
                        "authors": "Yazarlar",
                        "has_target_affil": "Kurum Eşleşmesi"
                    })

                    cols_order = ["Başlık", "Dergi", "Yıl", "Tip", "Atıf", "DOI", "Scopus ID", "Yazarlar", "Kurum Eşleşmesi", "doi_link"]
                    cols_order = [c for c in cols_order if c in df_display.columns]

                    st.dataframe(
                        df_display[cols_order],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "DOI": st.column_config.LinkColumn(
                                "DOI",
                                help="Makaleye gitmek için tıklayın",
                                display_text=r"https://doi\.org/(.*)"
                            ),
                            "doi_link": st.column_config.LinkColumn(
                                "Bağlantı",
                                display_text="Makaleye Git"
                            )
                        }
                    )

                    # Export Buttons
                    st.write("---")
                    st.subheader("Dışa Aktar")
                    c_dl1, c_dl2 = st.columns(2)

                    # CSV Export
                    csv = df_display[cols_order].to_csv(index=False).encode('utf-8-sig')
                    with c_dl1:
                        st.download_button(
                            "CSV Olarak İndir",
                            data=csv,
                            file_name="scopus_sonuclari.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    # Excel Export
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_display[cols_order].to_excel(writer, index=False, sheet_name='Sonuçlar')

                    with c_dl2:
                        st.download_button(
                            "Excel Olarak İndir",
                            data=buffer.getvalue(),
                            file_name="scopus_sonuclari.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                # --- Tab 2: Visualization ---
                with tab2:
                    st.subheader("Yayın İstatistikleri")

                    if "date" in df.columns:
                        df["date_dt"] = pd.to_datetime(df["date"], errors='coerce')

                        viz_type = st.radio("Gruplama Aralığı", ["Aylık", "Yıllık"], horizontal=True)

                        if viz_type == "Aylık":
                            df["period"] = df["date_dt"].dt.to_period("M").astype(str)
                        else:
                            df["period"] = df["date_dt"].dt.to_period("Y").astype(str)

                        chart_data = df.groupby("period").size().reset_index(name="Yayın Sayısı")

                        st.bar_chart(chart_data, x="period", y="Yayın Sayısı", color="#4b8bbe")

                    else:
                        st.warning("Tarih verisi bulunamadığı için grafik oluşturulamadı.")

            else:
                st.warning("Kriterlere uygun yayın bulunamadı.")

import streamlit as st
import pandas as pd
import io
import os

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Rekap Data SDMK Fasyankes DIY",
    page_icon="🏛️",
    layout="wide"
)

# --- STYLING CSS KHAS MODERN DIY ---
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .diy-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%);
        padding: 25px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .diy-header h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .diy-header p {
        margin: 5px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER UTAMA ---
st.markdown("""
    <div class="diy-header">
        <h1>🏛️ Portal Konsolidasi & QC SDMK Fasyankes DIY</h1>
        <p>Dinas Kesehatan Daerah Istimewa Yogyakarta • Kustomisasi Kolom & Transformasi Data</p>
    </div>
""", unsafe_allow_html=True)

# --- PANEL KONTROL & PILIHAN KOLOM (SIDEBAR) ---
st.sidebar.markdown("### ⚙️ Panel Kontrol & Pengaturan")
st.sidebar.markdown("---")

uploaded_files = st.sidebar.file_uploader(
    "1️⃣ Pilih Berkas Laporan (.xls / .html)", 
    type=["xls", "html"], 
    accept_multiple_files=True
)

master_file = st.sidebar.file_uploader(
    "2️⃣ Pilih Berkas Master Fasyankes (.xlsx)", 
    type=["xlsx"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Pilih Kolom Output Target")
st.sidebar.caption("Centang kolom yang ingin Anda sertakan dalam file hasil:")

# Daftar master kolom yang tersedia (NIK secara default tidak dicentang / dihilangkan)
available_columns = {
    "kode_unit": ("Kode Fasyankes", True),
    "nama_unit": ("Nama Fasyankes", True),
    "tanggal_lahir": ("Tanggal Lahir", True),
    "nama": ("Nama Lengkap", True),
    "jenis_tenaga": ("Jenis Tenaga", True),
    "status_pegawai": ("Status Pegawai", True),
    "jenis_kelamin": ("Jenis Kelamin", True),
    "nomor_str": ("Nomor STR", True),
    "status_str": ("Status STR", True),
    "nomor_sip": ("Nomor SIP", True),
    "tanggal_terbit_sip": ("Tanggal Terbit SIP", True),
    "tanggal_berakhir_sip": ("Tanggal Berakhir SIP", True),
    "nik": ("NIK (Nomor Induk Kependudukan)", False) # Default False (dihilangkan)
}

selected_target_cols = {}
for col_key, (col_label, default_val) in available_columns.items():
    if st.sidebar.checkbox(col_label, value=default_val):
        selected_target_cols[col_key] = col_label

# --- TOMBOL UTAMA ---
if st.button("🚀 GABUNGKAN & PROSES DATA SEKARANG", type="primary", use_container_width=True):
    if not uploaded_files or not master_file:
        st.error("⚠️ Harap unggah berkas laporan fasyankes dan master fasyankes terlebih dahulu melalui panel samping!")
    elif not selected_target_cols:
        st.error("⚠️ Pilih minimal satu kolom target output di panel samping!")
    else:
        with st.spinner("Sedang memproses konsolidasi, pembersihan teks, dan audit kualitas data..."):
            try:
                # 1. Membaca File Laporan
                data_frames = []
                for uploaded_file in uploaded_files:
                    try:
                        bytes_data = uploaded_file.getvalue()
                        html_content = bytes_data.decode('utf-8', errors='replace')
                        
                        dfs = pd.read_html(io.StringIO(html_content))
                        if len(dfs) > 0:
                            df = dfs[0]
                            if "No" in str(df.iloc[0, 0]) or "Nama Fasyankes" in str(df.iloc[0, 1]):
                                df.columns = df.iloc[0]
                                df = df[1:].reset_index(drop=True)
                            data_frames.append(df)
                    except Exception as e:
                        st.warning(f"Gagal membaca {uploaded_file.name}: {e}")

                if not data_frames:
                    st.error("Tidak ada data valid yang berhasil diekstrak.")
                else:
                    df_raw = pd.concat(data_frames, ignore_index=True)

                    # 2. Membaca Master Fasyankes
                    df_master = pd.read_excel(master_file)

                    # 3. Normalisasi & Joining Aman
                    col_raw = "Nama Fasyankes"
                    col_m = "Nama Fasyankes"

                    if col_raw in df_raw.columns and col_m in df_master.columns:
                        df_raw['_join_temp'] = df_raw[col_raw].astype(str).str.strip().str.lower()
                        df_master['_join_temp'] = df_master[col_m].astype(str).str.strip().str.lower()
                        
                        df_master = df_master.drop_duplicates(subset=['_join_temp'])

                        df_merged = pd.merge(
                            df_raw,
                            df_master,
                            on="_join_temp",
                            how="left",
                            suffixes=("", "_master"),
                        ).drop(columns=['_join_temp'])

                        if f"{col_raw}_master" in df_merged.columns:
                            df_merged[col_raw] = df_merged[f"{col_raw}_master"].fillna(df_merged[col_raw])
                    else:
                        df_merged = pd.merge(df_raw, df_master, on="Nama Fasyankes", how="left", suffixes=("", "_master"))

                    # 4. Fungsi Pembersih String Aman
                    def force_string(val):
                        if pd.isna(val) or val is None or str(val).lower() == 'nan':
                            return None
                        val_str = str(val).strip()
                        if val_str.endswith(".0"):
                            val_str = val_str[:-2]
                        if val_str.startswith("="):
                            val_str = "'" + val_str
                        return val_str

                    # 5. Konfigurasi Pemetaan Sumber ke Target
                    mapping_config = {
                        "kode_unit": ("Master Fasyankes", "Kode", "Teks Bersih"),
                        "nama_unit": ("Laporan Fasyankes", "Nama Fasyankes", "Teks"),
                        "nik": ("Laporan Fasyankes", "NIK", "Teks Bersih"),
                        "tanggal_lahir": ("Laporan Fasyankes", "Tanggal Lahir", "Tanggal (DD-MM-YYYY)"),
                        "nama": ("Laporan Fasyankes", "Nama Lengkap", "Teks"),
                        "jenis_tenaga": ("Laporan Fasyankes", "Jenis Tenaga", "Teks"),
                        "status_pegawai": ("Laporan Fasyankes", "Status", "Teks"),
                        "jenis_kelamin": ("Laporan Fasyankes", "Jenis Kelamin", "Teks"),
                        "nomor_str": ("Laporan Fasyankes", "Nomor STR", "Teks Bersih"),
                        "status_str": ("Laporan Fasyankes", "Status STR", "Teks"),
                        "nomor_sip": ("Laporan Fasyankes", "Nomor SIP", "Teks Bersih"),
                        "tanggal_terbit_sip": ("Laporan Fasyankes", "Tanggal Terbit SIP", "Tanggal (DD-MM-YYYY)"),
                        "tanggal_berakhir_sip": ("Laporan Fasyankes", "Tanggal Berakhir SIP", "Tanggal (DD-MM-YYYY)"),
                    }

                    df_final = pd.DataFrame()
                    df_final["no"] = range(1, len(df_merged) + 1)
                    target_to_tipe = {}

                    # Hanya proses kolom yang dicentang oleh user
                    for target_key in selected_target_cols.keys():
                        if target_key in mapping_config:
                            _, asal, tipe = mapping_config[target_key]
                            target_to_tipe[target_key] = tipe

                            if asal in df_merged.columns:
                                if tipe == "Tanggal (DD-MM-YYYY)":
                                    df_final[target_key] = pd.to_datetime(df_merged[asal], errors="coerce")
                                elif tipe == "Angka":
                                    df_final[target_key] = pd.to_numeric(df_merged[asal], errors="coerce")
                                else:
                                    df_final[target_key] = df_merged[asal].apply(force_string)
                            else:
                                df_final[target_key] = None

                    # 6. Analisis QC (Data Kosong)
                    df_tanpa_kode = pd.DataFrame()
                    if "kode_unit" in df_final.columns and "nama_unit" in df_final.columns:
                        mask_kode = df_final["kode_unit"].isna() | (df_final["kode_unit"] == "")
                        faskes_list = df_final[mask_kode]["nama_unit"].dropna().unique()
                        df_tanpa_kode = pd.DataFrame({"Nama_Fasyankes_Tanpa_Kode": sorted(faskes_list)})

                    df_tanpa_tgl = pd.DataFrame()
                    if "tanggal_lahir" in df_final.columns:
                        mask_tgl = df_final["tanggal_lahir"].isna()
                        cols_tgl = [c for c in ["no", "nama", "nama_unit", "jenis_tenaga", "tanggal_lahir"] if c in df_final.columns]
                        df_tanpa_tgl = df_final[mask_tgl][cols_tgl]

                    # 7. Generate Excel dengan Lebar Kolom Otomatis (Auto-Fit)
                    output_buffer = io.BytesIO()
                    with pd.ExcelWriter(
                        output_buffer,
                        engine="openpyxl",
                        date_format="DD-MM-YYYY",
                        datetime_format="DD-MM-YYYY",
                    ) as writer:
                        
                        sheets_data = {
                            "Data_Clean": df_final,
                            "Error_Tanpa_Kode_Unit": df_tanpa_kode,
                            "Error_Tanpa_Tgl_Lahir": df_tanpa_tgl
                        }

                        for sheet_name, dframe in sheets_data.items():
                            if not dframe.empty:
                                dframe.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        wb = writer.book
                        
                        if "Data_Clean" in wb.sheetnames:
                            ws = wb["Data_Clean"]
                            for col in ws.iter_cols(min_row=2):
                                col_name = ws.cell(row=1, column=col[0].column).value
                                tipe_aturan = target_to_tipe.get(col_name, "Teks") if col_name != "no" else "Angka"

                                if tipe_aturan == "Tanggal (DD-MM-YYYY)":
                                    for cell in col:
                                        if cell.value is not None:
                                            cell.number_format = "DD-MM-YYYY"
                                elif tipe_aturan == "Angka":
                                    for col_cell in col:
                                        if col_cell.value is not None:
                                            col_cell.number_format = "0"
                                else:
                                    for col_cell in col:
                                        if col_cell.value is not None:
                                            col_cell.number_format = '@'

                        # Auto-fit width untuk semua sheet
                        for sheetname in wb.sheetnames:
                            worksheet = wb[sheetname]
                            for col in worksheet.columns:
                                max_length = 0
                                column_letter = col[0].column_letter
                                for cell in col:
                                    try:
                                        if cell.value:
                                            cell_length = len(str(cell.value))
                                            if cell_length > max_length:
                                                max_length = cell_length
                                    except:
                                        pass
                                adjusted_width = max(max_length + 4, 12)
                                worksheet.column_dimensions[column_letter].width = adjusted_width

                    output_buffer.seek(0)

                    # Tampilan Statistik & Tombol Unduh
                    st.success("✨ Konsolidasi berhasil dengan kustomisasi kolom pilihan Anda!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Pegawai Terstruktur", f"{len(df_final):,} Baris".replace(",", "."))
                    with col2:
                        st.metric("Fasyankes Tanpa Kode", f"{len(df_tanpa_kode)} Unit")
                    with col3:
                        st.metric("Pegawai Tanpa Tgl Lahir", f"{len(df_tanpa_tgl)} Orang")

                    st.markdown("---")
                    st.download_button(
                        label="📥 Unduh File Excel Profesional (Rapi & Sesuai Pilihan Kolom)",
                        data=output_buffer,
                        file_name="Data_Pegawai_Final_DIY.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"Terjadi kesalahan teknis sistem: {e}")

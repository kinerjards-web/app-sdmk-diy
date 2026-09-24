import streamlit as st
import pandas as pd
import io
import os
import base64
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Rekap Data SDMK Fasyankes DIY",
    page_icon="🏛️",
    layout="wide"
)

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_data():
    st.session_state.uploader_key += 1

# --- INISIALISASI SESSION STATE UNTUK MAPPING KOLOM DINAMIS ---
if "mapping_df" not in st.session_state:
    default_mapping = [
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Kode", "Kolom Target": "kode_unit", "Tipe Format": "Teks Bersih"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Nama Fasyankes", "Kolom Target": "nama_unit", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "NIK", "Kolom Target": "nik", "Tipe Format": "Teks Bersih"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Tanggal Lahir", "Kolom Target": "tanggal_lahir", "Tipe Format": "Tanggal (DD-MM-YYYY)"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Nama Lengkap", "Kolom Target": "nama", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Jenis Tenaga", "Kolom Target": "jenis_tenaga", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Status", "Kolom Target": "status_pegawai", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Jenis Kelamin", "Kolom Target": "jenis_kelamin", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Nomor STR", "Kolom Target": "nomor_str", "Tipe Format": "Teks Bersih"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Status STR", "Kolom Target": "status_str", "Tipe Format": "Teks"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Nomor SIP", "Kolom Target": "nomor_sip", "Tipe Format": "Teks Bersih"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Tanggal Terbit SIP", "Kolom Target": "tanggal_terbit_sip", "Tipe Format": "Tanggal (DD-MM-YYYY)"},
        {"Sumber": "Laporan Fasyankes", "Kolom Asal": "Tanggal Berakhir SIP", "Kolom Target": "tanggal_berakhir_sip", "Tipe Format": "Tanggal (DD-MM-YYYY)"},
        # --- Atribut Master SDMK & Profil Fasyankes ---
        {"Sumber": "Master SDMK", "Kolom Asal": "Tenaga", "Kolom Target": "Tenaga", "Tipe Format": "Teks"},
        {"Sumber": "Master SDMK", "Kolom Asal": "subrumpun_sdmk", "Kolom Target": "subrumpun_sdmk", "Tipe Format": "Teks"},
        {"Sumber": "Master SDMK", "Kolom Asal": "rumpun_sdmk", "Kolom Target": "rumpun_sdmk", "Tipe Format": "Teks"},
        {"Sumber": "Master SDMK", "Kolom Asal": "kategori_sdmk", "Kolom Target": "kategori_sdmk", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Alamat", "Kolom Target": "Alamat", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Tipe", "Kolom Target": "Tipe", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Jenis", "Kolom Target": "Jenis", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Tingkatan", "Kolom Target": "Tingkatan", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "Penyelenggara", "Kolom Target": "Penyelenggara", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "latitude", "Kolom Target": "latitude", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "longitude", "Kolom Target": "longitude", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "desa", "Kolom Target": "desa", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "kec", "Kolom Target": "kec", "Tipe Format": "Teks"},
        {"Sumber": "Master Fasyankes", "Kolom Asal": "kab", "Kolom Target": "kab", "Tipe Format": "Teks"},
    ]
    st.session_state.mapping_df = pd.DataFrame(default_mapping)

# --- FUNGSI PEMBACA LOGO (BASE64) ---
@st.cache_data
def get_image_base64(file_path):
    try:
        with open(file_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return ""

logo_b64 = get_image_base64("logo_diy.jpg")

# --- STYLING CSS KHAS MODERN DIY ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .diy-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%);
        padding: 20px 30px; border-radius: 12px; color: white;
        margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        display: flex; align-items: center; 
    }
    .diy-header img { width: 75px; height: auto; margin-right: 25px; }
    .diy-header h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 0.5px; }
    .diy-header p { margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }
    hr { margin-top: 10px; margin-bottom: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if logo_b64:
    header_html = f"""
        <div class="diy-header">
            <img src="data:image/jpeg;base64,{logo_b64}" alt="Logo Pemda DIY">
            <div>
                <h1>Portal Konsolidasi & QC SDMK Fasyankes DIY</h1>
                <p>Dinas Kesehatan DIY • Dynamic Multi-Master ETL Pipeline</p>
            </div>
        </div>
    """
else:
    header_html = """
        <div class="diy-header">
            <div>
                <h1>🏛️ Portal Konsolidasi & QC SDMK Fasyankes DIY</h1>
                <p>Dinas Kesehatan DIY • Dynamic Multi-Master ETL Pipeline</p>
            </div>
        </div>
    """
st.markdown(header_html, unsafe_allow_html=True)

# =====================================================================
# SIDEBAR: PANEL INPUT BERKAS
# =====================================================================
st.sidebar.markdown("### ⚙️ Panel Input Berkas")
st.sidebar.markdown("---")

uploaded_files = st.sidebar.file_uploader(
    "📄 1. Laporan Fasyankes (.xls / .html)", 
    type=["xls", "html", "xlsx"], 
    accept_multiple_files=True,
    key=f"laporan_{st.session_state.uploader_key}"
)

master_file = st.sidebar.file_uploader(
    "🏥 2. Master Fasyankes (.xlsx)", 
    type=["xlsx"],
    key=f"master_{st.session_state.uploader_key}"
)

master_sdmk_file = st.sidebar.file_uploader(
    "⚕️ 3. Master Kode SDMK (.xlsx)", 
    type=["xlsx"],
    key=f"mastersdmk_{st.session_state.uploader_key}",
    help="Dibutuhkan jika Anda melakukan mapping kolom dari Master SDMK."
)

if st.sidebar.button("🗑️ Reset / Hapus Data Unggahan", use_container_width=True):
    reset_data()
    st.rerun()

# =====================================================================
# FUNGSI UTAMA ETL PIPELINE (BERBASIS MAPPING DINAMIS)
# =====================================================================
def jalankan_pipeline_dinamis(files_laporan, file_m_faskes, file_m_sdmk, df_mapping_rules):
    if not files_laporan or not file_m_faskes:
        st.error("⚠️ Harap unggah berkas Laporan dan Master Fasyankes terlebih dahulu!")
        return
    
    with st.spinner("Menjalankan Pipeline ETL Berbasis Mapping Dinamis..."):
        try:
            # TAHAP 1: BACA LAPORAN FASYANKES (SMART HEADER)
            data_frames = []
            for up_file in files_laporan:
                df_temp = None
                try:
                    bytes_data = up_file.getvalue()
                    try:
                        html_content = bytes_data.decode('utf-8', errors='replace')
                        dfs = pd.read_html(io.StringIO(html_content), flavor=['lxml', 'bs4', 'html5lib'])
                        if len(dfs) > 0: df_temp = dfs[0]
                    except Exception: pass
                        
                    if df_temp is None or df_temp.empty:
                        up_file.seek(0)
                        try: df_temp = pd.read_excel(up_file)
                        except Exception: pass
                            
                    if df_temp is not None and not df_temp.empty:
                        header_found = False
                        if any("nama fasyankes" in str(c).lower() for c in df_temp.columns):
                            header_found = True
                        else:
                            for idx, row in df_temp.head(15).iterrows():
                                if any("nama fasyankes" in str(val).lower() for val in row.values):
                                    df_temp.columns = row
                                    df_temp = df_temp.iloc[idx+1:].reset_index(drop=True)
                                    header_found = True
                                    break
                                    
                        if header_found:
                            data_frames.append(df_temp)
                except Exception: pass

            if not data_frames:
                st.error("❌ Seluruh berkas laporan dilewati karena format tidak dikenali/kosong.")
                return
            df_raw = pd.concat(data_frames, ignore_index=True)

            # TAHAP 2: BACA & JOIN MASTER FASYANKES
            df_master = pd.read_excel(file_m_faskes)
            h_found = False
            if any("nama fasyankes" in str(c).lower() for c in df_master.columns):
                h_found = True
            else:
                for idx, row in df_master.head(15).iterrows():
                    if any("nama fasyankes" in str(val).lower() for val in row.values):
                        df_master.columns = row
                        df_master = df_master.iloc[idx+1:].reset_index(drop=True)
                        h_found = True
                        break
                        
            if not h_found:
                st.error("❌ Gagal: Kolom 'Nama Fasyankes' tidak terdeteksi di Master Fasyankes.")
                return

            col_raw_faskes = next((c for c in df_raw.columns if "nama fasyankes" in str(c).lower()), None)
            col_m_faskes = next((c for c in df_master.columns if "nama fasyankes" in str(c).lower()), None)

            if col_raw_faskes and col_m_faskes:
                df_raw['_j'] = df_raw[col_raw_faskes].astype(str).str.strip().str.lower()
                df_master['_j'] = df_master[col_m_faskes].astype(str).str.strip().str.lower()
                df_master = df_master.drop_duplicates(subset=['_j'])
                df_merged = pd.merge(df_raw, df_master, on="_j", how="left", suffixes=("", "_master")).drop(columns=['_j'])
            else:
                st.error("❌ Kolom 'Nama Fasyankes' tidak ditemukan untuk proses joining.")
                return

            # TAHAP 3: BACA & JOIN MASTER SDMK (JIKA ADA)
            if file_m_sdmk is not None:
                try:
                    df_sdmk = pd.read_excel(file_m_sdmk)
                    col_raw_tenaga = next((c for c in df_merged.columns if "jenis tenaga" in str(c).lower()), None)
                    col_m_tenaga = next((c for c in df_sdmk.columns if "jenis tenaga" in str(c).lower()), None)
                    
                    if col_raw_tenaga and col_m_tenaga:
                        df_merged['_j_sdmk'] = df_merged[col_raw_tenaga].astype(str).str.strip().str.lower()
                        df_sdmk['_j_sdmk'] = df_sdmk[col_m_tenaga].astype(str).str.strip().str.lower()
                        df_sdmk = df_sdmk.drop_duplicates(subset=['_j_sdmk'])
                        df_merged = pd.merge(df_merged, df_sdmk, on="_j_sdmk", how="left", suffixes=("", "_sdmk")).drop(columns=['_j_sdmk'])
                except Exception:
                    pass

            # TAHAP 4: PEMBUATAN UID & LOG TANGGAL PROSES OTOMATIS
            col_nama_lengkap = next((c for c in df_merged.columns if "nama lengkap" in str(c).lower() or c.lower() == "nama"), None)
            col_tgl_lahir = next((c for c in df_merged.columns if "tanggal lahir" in str(c).lower()), None)

            if col_nama_lengkap and col_tgl_lahir:
                clean_nama = df_merged[col_nama_lengkap].astype(str).str.replace(r'[^a-zA-Z]', '', regex=True).str.upper()
                clean_tgl = pd.to_datetime(df_merged[col_tgl_lahir], errors='coerce').dt.strftime('%d%m%Y').fillna('00000000')
                df_merged["UID"] = clean_nama + "_" + clean_tgl
            else:
                df_merged["UID"] = None
                
            df_merged["Tanggal Proses"] = pd.Timestamp.now().strftime("%d-%m-%Y %H:%M")

            # TAHAP 5: PEMETAAN KOLOM BERDASARKAN TABEL MAPPING DINAMIS
            def force_string(val):
                if pd.isna(val) or val is None or str(val).lower() == 'nan': return None
                val_str = str(val).strip()
                if val_str.endswith(".0"): val_str = val_str[:-2]
                if val_str.startswith("="): val_str = "'" + val_str
                return val_str

            df_final = pd.DataFrame()
            # Kolom nomor urut murni dari sistem (1, 2, 3...)
            df_final["no"] = range(1, len(df_merged) + 1)
            
            # Tambahkan Kolom Wajib UID di Urutan Pertama (Sebelum kolom lain)
            df_final["uid"] = df_merged["UID"]

            type_mapping_registry = {"no": "Angka", "uid": "Teks"}

            for _, row in df_mapping_rules.iterrows():
                t_target = str(row["Kolom Target"]).strip()
                c_asal = str(row["Kolom Asal"]).strip()
                t_format = str(row["Tipe Format"]).strip()
                
                # Cegah duplikasi jika kolom uid sudah dipasang otomatis
                if t_target.lower() == "uid":
                    continue

                type_mapping_registry[t_target] = t_format

                if t_target.lower() in ["tanggal proses", "log tanggal proses"]:
                    df_final[t_target] = df_merged["Tanggal Proses"]
                    continue

                # Cari kolom asal secara fleksibel (case-insensitive)
                match_col = next((c for c in df_merged.columns if str(c).lower() == c_asal.lower()), None)

                if match_col:
                    if "tanggal" in t_format.lower() or t_format.lower() == "tgl":
                        df_final[t_target] = pd.to_datetime(df_merged[match_col], errors="coerce")
                    else:
                        df_final[t_target] = df_merged[match_col].apply(force_string)
                else:
                    df_final[t_target] = None

            # TAHAP 6: QUALITY CONTROL (QC)
            df_no_kode = pd.DataFrame()
            col_kode_res = next((c for c in df_final.columns if "kode" in str(c).lower()), None)
            col_nama_res = next((c for c in df_final.columns if "nama_unit" in str(c).lower() or "fasyankes" in str(c).lower()), None)
            if col_kode_res and col_nama_res:
                m_kode = df_final[col_kode_res].isna() | (df_final[col_kode_res] == "")
                df_no_kode = pd.DataFrame({"Nama_Fasyankes_Tanpa_Kode": sorted(df_final[m_kode][col_nama_res].dropna().unique())})
            
            df_no_tgl = pd.DataFrame()
            col_tgl_res = next((c for c in df_final.columns if "tanggal_lahir" in str(c).lower()), None)
            if col_tgl_res:
                df_no_tgl = df_final[df_final[col_tgl_res].isna()]

            # TAHAP 7: EXCEL GENERATION DENGAN AUTO-FIT
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine="openpyxl", date_format="DD-MM-YYYY", datetime_format="DD-MM-YYYY") as writer:
                sheets_data = {"Data_Clean": df_final, "Error_Tanpa_Kode": df_no_kode, "Error_Tanpa_Tgl_Lahir": df_no_tgl}
                for s_name, dframe in sheets_data.items():
                    if not dframe.empty: dframe.to_excel(writer, sheet_name=s_name, index=False)
                
                wb = writer.book
                if "Data_Clean" in wb.sheetnames:
                    ws = wb["Data_Clean"]
                    for col in ws.iter_cols(min_row=2):
                        c_name = ws.cell(row=1, column=col[0].column).value
                        fmt = type_mapping_registry.get(c_name, "Teks")
                        if "tanggal" in str(fmt).lower():
                            for cell in col:
                                if cell.value: cell.number_format = "DD-MM-YYYY"
                        elif c_name == "no":
                            for cell in col:
                                if cell.value: cell.number_format = "0"
                        else:
                            for cell in col:
                                if cell.value: cell.number_format = '@'

                for s_name in wb.sheetnames:
                    worksheet = wb[s_name]
                    for col in worksheet.columns:
                        max_len = 0
                        col_let = col[0].column_letter
                        for cell in col:
                            try:
                                if cell.value and len(str(cell.value)) > max_len: max_len = len(str(cell.value))
                            except: pass
                        worksheet.column_dimensions[col_let].width = max(max_len + 4, 12)
            output_buffer.seek(0)
            
            # TAMPILAN HASIL
            st.success("✨ Konsolidasi ETL Berbasis Mapping Dinamis Berhasil!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Pegawai Terstruktur", f"{len(df_final):,} Baris".replace(",", "."))
            c2.metric("Fasyankes Tanpa Kode", f"{len(df_no_kode)} Unit")
            c3.metric("Pegawai Tanpa Tgl Lahir", f"{len(df_no_tgl)} Orang")
            st.markdown("---")
            st.download_button(
                label="📥 Unduh File Excel Hasil Dinamis", 
                data=output_buffer, 
                file_name="Data_Pegawai_Dinamis_DIY.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan teknis: {e}")

# =====================================================================
# MAIN AREA: SISTEM TABS (TAB 1: EKSEKUSI, TAB 2: PENGATURAN KOLOM)
# =====================================================================
tab_eksekusi, tab_mapping = st.tabs([
    "🚀 1. Eksekusi Pipeline & Unduh", 
    "⚙️ 2. Pengaturan & Mapping Kolom Dinamis"
])

# ----------------- KONTEN TAB 1: EKSEKUSI -----------------
with tab_eksekusi:
    st.info("💡 **Halaman Eksekusi**: Pastikan aturan mapping kolom di Tab sebelah sudah sesuai dengan kebutuhan Anda.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🚀 JALANKAN PROSES ETL SEKARANG", type="primary", use_container_width=True):
        jalankan_pipeline_dinamis(uploaded_files, master_file, master_sdmk_file, st.session_state.mapping_df)

# ----------------- KONTEN TAB 2: MAPPING MANAGER -----------------
with tab_mapping:
    st.subheader("🛠️ Manajer Pengaturan Kolom Input & Master")
    st.markdown(
        "Di bawah ini adalah daftar kolom yang akan diekstrak dan digabungkan ke file Excel hasil. "
        "Kolom **`no`** (nomor urut otomatis) dan **`uid`** (ID unik pegawai) sudah otomatis dipasang oleh sistem di bagian paling depan."
    )
    
    edited_df = st.data_editor(
        st.session_state.mapping_df,
        num_rows="dynamic",
        column_config={
            "Sumber": st.column_config.SelectboxColumn(
                "Sumber Data",
                options=["Laporan Fasyankes", "Master Fasyankes", "Master SDMK"],
                required=True
            ),
            "Tipe Format": st.column_config.SelectboxColumn(
                "Tipe Format",
                options=["Teks", "Tanggal (DD-MM-YYYY)", "Teks Bersih", "Angka"],
                required=True
            )
        },
        use_container_width=True,
        key="editor_mapping"
    )
    
    st.session_state.mapping_df = edited_df
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Reset Pengaturan Kolom ke Default", use_container_width=True):
            del st.session_state.mapping_df
            st.rerun()
    with col_btn2:
        st.success("✅ Perubahan pada tabel di atas otomatis tersimpan untuk proses berikutnya.")

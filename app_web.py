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
                <p>Dinas Kesehatan DIY • Ultimate Multi-Master ETL Pipeline</p>
            </div>
        </div>
    """
else:
    header_html = """
        <div class="diy-header">
            <div>
                <h1>🏛️ Portal Konsolidasi & QC SDMK Fasyankes DIY</h1>
                <p>Dinas Kesehatan DIY • Ultimate Multi-Master ETL Pipeline</p>
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
    "⚕️ 3. Master SDMK (.xlsx)", 
    type=["xlsx"],
    key=f"mastersdmk_{st.session_state.uploader_key}",
    help="Hanya dibutuhkan jika Anda memproses Mode Super Lengkap."
)

if st.sidebar.button("🗑️ Reset / Hapus Data Unggahan", use_container_width=True):
    reset_data()
    st.rerun()

# =====================================================================
# FUNGSI UTAMA ETL PIPELINE (STABLE VERSION)
# =====================================================================
def jalankan_pipeline(mode, files_laporan, file_m_faskes, file_m_sdmk, target_cols):
    if not files_laporan or not file_m_faskes:
        st.error("⚠️ Harap unggah berkas Laporan dan Master Fasyankes terlebih dahulu!")
        return
    if mode == "lengkap" and not file_m_sdmk:
        st.error("⚠️ Untuk Mode Lengkap, berkas Master Kode SDMK Wajib Diunggah di panel samping!")
        return
    if not target_cols:
        st.error("⚠️ Pilih minimal satu kolom target output!")
        return

    with st.spinner(f"Menjalankan Pipeline ETL ({mode.upper()})..."):
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
                            rename_dict = {}
                            for col in df_temp.columns:
                                c_str = str(col).lower().strip()
                                if "nama fasyankes" in c_str: rename_dict[col] = "Nama Fasyankes"
                                elif c_str == "nik": rename_dict[col] = "NIK"
                                elif "tanggal lahir" in c_str: rename_dict[col] = "Tanggal Lahir"
                                elif "nama lengkap" in c_str or c_str == "nama": rename_dict[col] = "Nama Lengkap"
                                elif "jenis tenaga" in c_str: rename_dict[col] = "Jenis Tenaga"
                                elif c_str == "status": rename_dict[col] = "Status"
                                elif "jenis kelamin" in c_str: rename_dict[col] = "Jenis Kelamin"
                                elif "nomor str" in c_str: rename_dict[col] = "Nomor STR"
                                elif "status str" in c_str: rename_dict[col] = "Status STR"
                                elif "nomor sip" in c_str: rename_dict[col] = "Nomor SIP"
                                elif "tanggal terbit sip" in c_str: rename_dict[col] = "Tanggal Terbit SIP"
                                elif "tanggal berakhir sip" in c_str: rename_dict[col] = "Tanggal Berakhir SIP"
                            df_temp = df_temp.rename(columns=rename_dict)
                            data_frames.append(df_temp)
                except Exception: pass

            if not data_frames:
                st.error("❌ Seluruh berkas dilewati karena format tidak dikenali/kosong.")
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

            r_master = {}
            for col in df_master.columns:
                c_str = str(col).lower().strip()
                if "nama fasyankes" in c_str: r_master[col] = "Nama Fasyankes"
                elif "kode" == c_str or "kode fasyankes" in c_str: r_master[col] = "Kode"
                elif c_str == "alamat": r_master[col] = "Alamat"
                elif c_str == "tipe": r_master[col] = "Tipe"
                elif c_str == "jenis": r_master[col] = "Jenis"
                elif c_str == "tingkatan": r_master[col] = "Tingkatan"
                elif c_str == "penyelenggara": r_master[col] = "Penyelenggara"
                elif "lat" in c_str: r_master[col] = "latitude"
                elif "long" in c_str: r_master[col] = "longitude"
                elif "desa" in c_str or "kelurahan" in c_str: r_master[col] = "desa"
                elif "kec" in c_str: r_master[col] = "kec"
                elif "kab" in c_str or "kota" in c_str: r_master[col] = "kab"
            df_master = df_master.rename(columns=r_master)

            if "Nama Fasyankes" in df_raw.columns and "Nama Fasyankes" in df_master.columns:
                df_raw['_j'] = df_raw["Nama Fasyankes"].astype(str).str.strip().str.lower()
                df_master['_j'] = df_master["Nama Fasyankes"].astype(str).str.strip().str.lower()
                df_master = df_master.drop_duplicates(subset=['_j'])
                df_merged = pd.merge(df_raw, df_master, on="_j", how="left", suffixes=("", "_master")).drop(columns=['_j'])
                if "Nama Fasyankes_master" in df_merged.columns:
                    df_merged["Nama Fasyankes"] = df_merged["Nama Fasyankes_master"].fillna(df_merged["Nama Fasyankes"])
            else:
                st.error("❌ Gagal Menggabungkan Data: Kolom 'Nama Fasyankes' hilang.")
                return

            # TAHAP 3: BACA & JOIN MASTER SDMK 
            if mode == "lengkap":
                df_sdmk = pd.read_excel(file_m_sdmk)
                r_sdmk = {}
                for col in df_sdmk.columns:
                    c_str = str(col).lower().strip()
                    if c_str == "jenis tenaga": r_sdmk[col] = "Jenis Tenaga"
                    elif c_str == "tenaga": r_sdmk[col] = "Tenaga"
                    elif c_str == "subrumpun_sdmk" or c_str == "subrumpun sdmk": r_sdmk[col] = "subrumpun_sdmk"
                    elif c_str == "rumpun_sdmk" or c_str == "rumpun sdmk": r_sdmk[col] = "rumpun_sdmk"
                    elif c_str == "kategori_sdmk" or c_str == "kategori sdmk": r_sdmk[col] = "kategori_sdmk"
                df_sdmk = df_sdmk.rename(columns=r_sdmk)

                if "Jenis Tenaga" in df_merged.columns and "Jenis Tenaga" in df_sdmk.columns:
                    df_merged['_j_sdmk'] = df_merged["Jenis Tenaga"].astype(str).str.strip().str.lower()
                    df_sdmk['_j_sdmk'] = df_sdmk["Jenis Tenaga"].astype(str).str.strip().str.lower()
                    df_sdmk = df_sdmk.drop_duplicates(subset=['_j_sdmk'])
                    df_merged = pd.merge(df_merged, df_sdmk, on="_j_sdmk", how="left", suffixes=("", "_sdmk")).drop(columns=['_j_sdmk'])

            # TAHAP 4: PEMBUATAN UID & LOG TANGGAL PROSES
            if "Nama Lengkap" in df_merged.columns and "Tanggal Lahir" in df_merged.columns:
                clean_nama = df_merged["Nama Lengkap"].astype(str).str.replace(r'[^a-zA-Z]', '', regex=True).str.upper()
                clean_tgl = pd.to_datetime(df_merged["Tanggal Lahir"], errors='coerce').dt.strftime('%d%m%Y').fillna('00000000')
                df_merged["UID"] = clean_nama + "_" + clean_tgl
            else:
                df_merged["UID"] = None
                
            df_merged["Tanggal Proses"] = pd.Timestamp.now().strftime("%d-%m-%Y %H:%M")

            # TAHAP 5: PEMETAAN KOLOM (MAPPING)
            def force_string(val):
                if pd.isna(val) or val is None or str(val).lower() == 'nan': return None
                val_str = str(val).strip()
                if val_str.endswith(".0"): val_str = val_str[:-2]
                if val_str.startswith("="): val_str = "'" + val_str
                return val_str

            map_cfg = {
                "uid": ("UID", "Teks"), 
                "kode_unit": ("Kode", "Teks"), 
                "nama_unit": ("Nama Fasyankes", "Teks"), 
                "nik": ("NIK", "Teks"),
                "tanggal_lahir": ("Tanggal Lahir", "Tgl"), 
                "nama": ("Nama Lengkap", "Teks"), # <--- Kolom nama dijamin terpisah & aman
                "jenis_tenaga": ("Jenis Tenaga", "Teks"),
                "status_pegawai": ("Status", "Teks"), 
                "jenis_kelamin": ("Jenis Kelamin", "Teks"), 
                "nomor_str": ("Nomor STR", "Teks"),
                "status_str": ("Status STR", "Teks"), 
                "nomor_sip": ("Nomor SIP", "Teks"),
                "tanggal_terbit_sip": ("Tanggal Terbit SIP", "Tgl"), 
                "tanggal_berakhir_sip": ("Tanggal Berakhir SIP", "Tgl"),
                "Tenaga": ("Tenaga", "Teks"), 
                "subrumpun_sdmk": ("subrumpun_sdmk", "Teks"), 
                "rumpun_sdmk": ("rumpun_sdmk", "Teks"),
                "kategori_sdmk": ("kategori_sdmk", "Teks"), 
                "Alamat": ("Alamat", "Teks"), 
                "Tipe": ("Tipe", "Teks"),
                "Jenis": ("Jenis", "Teks"), 
                "Tingkatan": ("Tingkatan", "Teks"), 
                "Penyelenggara": ("Penyelenggara", "Teks"),
                "latitude": ("latitude", "Teks"), 
                "longitude": ("longitude", "Teks"), 
                "desa": ("desa", "Teks"),
                "kec": ("kec", "Teks"), 
                "kab": ("kab", "Teks"), 
                "tanggal_proses": ("Tanggal Proses", "Teks")
            }

            df_final = pd.DataFrame()
            df_final["no"] = range(1, len(df_merged) + 1)
            t_to_type = {}

            for tk in target_cols.keys():
                if tk in map_cfg:
                    asal, tipe = map_cfg[tk]
                    t_to_type[tk] = tipe
                    if asal in df_merged.columns:
                        if tipe == "Tgl": df_final[tk] = pd.to_datetime(df_merged[asal], errors="coerce")
                        else: df_final[tk] = df_merged[asal].apply(force_string)
                    else:
                        df_final[tk] = None

            # TAHAP 6: QUALITY CONTROL (QC)
            df_no_kode = pd.DataFrame()
            if "kode_unit" in df_final.columns and "nama_unit" in df_final.columns:
                m_kode = df_final["kode_unit"].isna() | (df_final["kode_unit"] == "")
                df_no_kode = pd.DataFrame({"Nama_Fasyankes_Tanpa_Kode": sorted(df_final[m_kode]["nama_unit"].dropna().unique())})
            
            df_no_tgl = pd.DataFrame()
            if "tanggal_lahir" in df_final.columns:
                df_no_tgl = df_final[df_final["tanggal_lahir"].isna()][[c for c in ["no","nama","nama_unit","jenis_tenaga","tanggal_lahir"] if c in df_final.columns]]

            # TAHAP 7: EXCEL GENERATION
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
                        if t_to_type.get(c_name, "Teks") == "Tgl":
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
            st.success(f"✨ Laporan {mode.title()} berhasil diproses!")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Pegawai Terstruktur", f"{len(df_final):,} Baris".replace(",", "."))
            c2.metric("Fasyankes Tanpa Kode", f"{len(df_no_kode)} Unit")
            c3.metric("Pegawai Tanpa Tgl Lahir", f"{len(df_no_tgl)} Orang")
            st.markdown("---")
            st.download_button(
                label=f"📥 Unduh File Excel ({mode.title()})", 
                data=output_buffer, 
                file_name=f"Data_Pegawai_{mode.title()}_DIY.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True
            )
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan teknis: {e}")

# =====================================================================
# MAIN AREA: SISTEM TABS (UI VERSI 5.3)
# =====================================================================
tab_standar, tab_lengkap = st.tabs([
    "📊 1. MODE LAPORAN STANDAR", 
    "🚀 2. MODE SUPER LENGKAP (SDMK + Geografis)"
])

# ----------------- KONTEN TAB 1 (STANDAR) -----------------
with tab_standar:
    st.info("💡 **Mode Laporan Standar**: Menghasilkan data rekapitulasi dasar pegawai dan unit fasyankes.")
    st.markdown("##### 📋 Sesuaikan Kolom Output")
    
    dict_standar = {
        "uid": ("UID Pegawai (Nama+TglLahir)", True),
        "kode_unit": ("Kode Fasyankes", True), 
        "nama_unit": ("Nama Fasyankes", True), 
        "tanggal_lahir": ("Tanggal Lahir", True),
        "nama": ("Nama Lengkap", True),  # <--- Ditampilkan secara terpisah dan aman
        "jenis_tenaga": ("Jenis Tenaga", True), 
        "status_pegawai": ("Status Pegawai", True),
        "jenis_kelamin": ("Jenis Kelamin", True), 
        "nomor_str": ("Nomor STR", True), 
        "status_str": ("Status STR", False),
        "nomor_sip": ("Nomor SIP", True), 
        "tanggal_terbit_sip": ("Tanggal Terbit SIP", True), 
        "tanggal_berakhir_sip": ("Tanggal Berakhir SIP", True),
        "nik": ("NIK (Nomor Induk)", False),
        "tanggal_proses": ("Log Tanggal Proses", True)
    }
    
    selected_std = {}
    cols_std = st.columns(3)
    for i, (k, (label, default)) in enumerate(dict_standar.items()):
        if cols_std[i % 3].checkbox(label, value=default, key=f"std_{k}"):
            selected_std[k] = label
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 GABUNGKAN & PROSES (MODE STANDAR)", type="primary", use_container_width=True):
        jalankan_pipeline("standar", uploaded_files, master_file, None, selected_std)


# ----------------- KONTEN TAB 2 (SUPER LENGKAP) -----------------
with tab_lengkap:
    st.info("💡 **Mode Super Lengkap**: Mengintegrasikan klasifikasi Profesi SDMK beserta Profil Detail & Koordinat Fasyankes.")
    st.markdown("##### 📋 Sesuaikan Kolom Output")
    
    dict_lengkap = {
        "uid": ("UID Pegawai (Nama+TglLahir)", True),
        "kode_unit": ("Kode Fasyankes", True), 
        "nama_unit": ("Nama Fasyankes", True), 
        "tanggal_lahir": ("Tanggal Lahir", True),
        "nama": ("Nama Lengkap", True),  # <--- Ditampilkan secara terpisah dan aman
        "jenis_tenaga": ("Jenis Tenaga", True), 
        "status_pegawai": ("Status Pegawai", True),
        "jenis_kelamin": ("Jenis Kelamin", True), 
        "nomor_str": ("Nomor STR", True), 
        "nomor_sip": ("Nomor SIP", True),
        "tanggal_terbit_sip": ("Tanggal Terbit SIP", True), 
        "tanggal_berakhir_sip": ("Tanggal Berakhir SIP", True),
        "Tenaga": ("Tenaga (SDMK)", True), 
        "subrumpun_sdmk": ("Subrumpun SDMK", True), 
        "rumpun_sdmk": ("Rumpun SDMK", True),
        "kategori_sdmk": ("Kategori SDMK", True), 
        "Alamat": ("Alamat", True), 
        "Tipe": ("Tipe Fasyankes", True),
        "Jenis": ("Jenis Fasyankes", True), 
        "Tingkatan": ("Tingkatan", True), 
        "Penyelenggara": ("Penyelenggara", True),
        "latitude": ("Latitude", True), 
        "longitude": ("Longitude", True), 
        "desa": ("Desa / Kelurahan", True),
        "kec": ("Kecamatan", True), 
        "kab": ("Kabupaten / Kota", True), 
        "status_str": ("Status STR", False), 
        "nik": ("NIK (Nomor Induk)", False),
        "tanggal_proses": ("Log Tanggal Proses", True)
    }
    
    selected_pro = {}
    cols_pro = st.columns(3)
    for i, (k, (label, default)) in enumerate(dict_lengkap.items()):
        if cols_pro[i % 3].checkbox(label, value=default, key=f"pro_{k}"):
            selected_pro[k] = label

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 GABUNGKAN & PROSES (MODE SUPER LENGKAP)", type="primary", use_container_width=True):
        jalankan_pipeline("lengkap", uploaded_files, master_file, master_sdmk_file, selected_pro)

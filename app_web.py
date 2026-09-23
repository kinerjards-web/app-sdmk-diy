import streamlit as st
import pandas as pd
import io
import os

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

# --- STYLING CSS KHAS MODERN DIY ---
st.markdown("""
    <style>
    .main { background-color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .diy-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0284c7 100%);
        padding: 25px 30px; border-radius: 12px; color: white;
        margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .diy-header h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 0.5px; }
    .diy-header p { margin: 5px 0 0 0; font-size: 14px; opacity: 0.9; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="diy-header">
        <h1>🏛️ Portal Konsolidasi & QC SDMK Fasyankes DIY</h1>
        <p>Dinas Kesehatan Daerah Istimewa Yogyakarta • Kustomisasi Kolom & Transformasi Data</p>
    </div>
""", unsafe_allow_html=True)

# --- PANEL KONTROL & UPLOAD (SIDEBAR) ---
st.sidebar.markdown("### ⚙️ Panel Kontrol & Pengaturan")
st.sidebar.markdown("---")

uploaded_files = st.sidebar.file_uploader(
    "1️⃣ Pilih Berkas Laporan (.xls / .html / .xlsx)", 
    type=["xls", "html", "xlsx"], 
    accept_multiple_files=True,
    key=f"laporan_{st.session_state.uploader_key}"
)

master_file = st.sidebar.file_uploader(
    "2️⃣ Pilih Berkas Master Fasyankes (.xlsx)", 
    type=["xlsx"],
    key=f"master_{st.session_state.uploader_key}"
)

if st.sidebar.button("🗑️ Reset / Hapus Data Unggahan", use_container_width=True):
    reset_data()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Pilih Kolom Output Target")

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
    "nik": ("NIK (Nomor Induk)", False) 
}

selected_target_cols = {}
for col_key, (col_label, default_val) in available_columns.items():
    if st.sidebar.checkbox(col_label, value=default_val):
        selected_target_cols[col_key] = col_label

# --- PROSES UTAMA ---
if st.button("🚀 GABUNGKAN & PROSES DATA SEKARANG", type="primary", use_container_width=True):
    if not uploaded_files or not master_file:
        st.error("⚠️ Harap unggah berkas laporan fasyankes dan master fasyankes terlebih dahulu!")
    elif not selected_target_cols:
        st.error("⚠️ Pilih minimal satu kolom target output di panel samping!")
    else:
        with st.spinner("Sedang memproses data..."):
            try:
                # 1. BACA & DETEKSI HEADER LAPORAN
                data_frames = []
                for uploaded_file in uploaded_files:
                    df_temp = None
                    try:
                        bytes_data = uploaded_file.getvalue()
                        
                        # A. Coba baca sebagai HTML
                        try:
                            html_content = bytes_data.decode('utf-8', errors='replace')
                            dfs = pd.read_html(io.StringIO(html_content), flavor=['lxml', 'bs4', 'html5lib'])
                            if len(dfs) > 0: df_temp = dfs[0]
                        except Exception:
                            pass
                            
                        # B. Coba baca sebagai Excel murni jika gagal
                        if df_temp is None or df_temp.empty:
                            uploaded_file.seek(0)
                            try:
                                df_temp = pd.read_excel(uploaded_file)
                            except Exception:
                                pass
                                
                        if df_temp is not None and not df_temp.empty:
                            # --- SMART HEADER DETECTOR ---
                            header_found = False
                            if any("nama fasyankes" in str(c).lower() for c in df_temp.columns):
                                header_found = True
                            else:
                                # Scan 15 baris pertama untuk mencari Header
                                for idx, row in df_temp.head(15).iterrows():
                                    if any("nama fasyankes" in str(val).lower() for val in row.values):
                                        df_temp.columns = row
                                        df_temp = df_temp.iloc[idx+1:].reset_index(drop=True)
                                        header_found = True
                                        break
                                        
                            if header_found:
                                # Standardisasi nama kolom secara otomatis (kebal huruf besar/kecil)
                                rename_dict = {}
                                for col in df_temp.columns:
                                    c_str = str(col).lower().strip()
                                    if "nama fasyankes" in c_str: rename_dict[col] = "Nama Fasyankes"
                                    elif c_str == "nik": rename_dict[col] = "NIK"
                                    elif "tanggal lahir" in c_str: rename_dict[col] = "Tanggal Lahir"
                                    elif "nama lengkap" in c_str: rename_dict[col] = "Nama Lengkap"
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
                            else:
                                st.warning(f"⚠️ Berkas '{uploaded_file.name}' dilewati: Kolom 'Nama Fasyankes' tidak ditemukan.")
                        else:
                            st.warning(f"⚠️ Berkas '{uploaded_file.name}' kosong atau rusak.")
                    except Exception as e:
                        st.warning(f"⚠️ Gagal membaca berkas '{uploaded_file.name}': {e}")

                if not data_frames:
                    st.error("❌ Seluruh berkas dilewati karena format tidak dikenali/kosong.")
                    st.stop()
                
                df_raw = pd.concat(data_frames, ignore_index=True)

                # 2. BACA & STANDARDISASI MASTER FASYANKES
                df_master = pd.read_excel(master_file)
                rename_master = {}
                for col in df_master.columns:
                    c_str = str(col).lower().strip()
                    if "nama fasyankes" in c_str: rename_master[col] = "Nama Fasyankes"
                    elif "kode" == c_str or "kode fasyankes" in c_str: rename_master[col] = "Kode"
                df_master = df_master.rename(columns=rename_master)

                # 3. PENGGABUNGAN (JOINING) AMAN
                if "Nama Fasyankes" in df_raw.columns and "Nama Fasyankes" in df_master.columns:
                    df_raw['_join_temp'] = df_raw["Nama Fasyankes"].astype(str).str.strip().str.lower()
                    df_master['_join_temp'] = df_master["Nama Fasyankes"].astype(str).str.strip().str.lower()
                    
                    df_master = df_master.drop_duplicates(subset=['_join_temp'])
                    df_merged = pd.merge(df_raw, df_master, on="_join_temp", how="left", suffixes=("", "_master"))
                    df_merged = df_merged.drop(columns=['_join_temp'])

                    if "Nama Fasyankes_master" in df_merged.columns:
                        df_merged["Nama Fasyankes"] = df_merged["Nama Fasyankes_master"].fillna(df_merged["Nama Fasyankes"])
                else:
                    st.error("❌ Gagal Menggabungkan Data: Kolom Utama 'Nama Fasyankes' tidak terdeteksi.")
                    st.stop()

                # 4. Fungsi Pembersih String
                def force_string(val):
                    if pd.isna(val) or val is None or str(val).lower() == 'nan': return None
                    val_str = str(val).strip()
                    if val_str.endswith(".0"): val_str = val_str[:-2]
                    if val_str.startswith("="): val_str = "'" + val_str
                    return val_str

                # 5. MAPPING KOLOM
                mapping_config = {
                    "kode_unit": ("Kode", "Teks Bersih"),
                    "nama_unit": ("Nama Fasyankes", "Teks"),
                    "nik": ("NIK", "Teks Bersih"),
                    "tanggal_lahir": ("Tanggal Lahir", "Tanggal (DD-MM-YYYY)"),
                    "nama": ("Nama Lengkap", "Teks"),
                    "jenis_tenaga": ("Jenis Tenaga", "Teks"),
                    "status_pegawai": ("Status", "Teks"),
                    "jenis_kelamin": ("Jenis Kelamin", "Teks"),
                    "nomor_str": ("Nomor STR", "Teks Bersih"),
                    "status_str": ("Status STR", "Teks"),
                    "nomor_sip": ("Nomor SIP", "Teks Bersih"),
                    "tanggal_terbit_sip": ("Tanggal Terbit SIP", "Tanggal (DD-MM-YYYY)"),
                    "tanggal_berakhir_sip": ("Tanggal Berakhir SIP", "Tanggal (DD-MM-YYYY)"),
                }

                df_final = pd.DataFrame()
                df_final["no"] = range(1, len(df_merged) + 1)
                target_to_tipe = {}

                for target_key in selected_target_cols.keys():
                    if target_key in mapping_config:
                        asal, tipe = mapping_config[target_key]
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

                # 6. ANALISIS QC
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

                # 7. EXPORT EXCEL
                output_buffer = io.BytesIO()
                with pd.ExcelWriter(output_buffer, engine="openpyxl", date_format="DD-MM-YYYY", datetime_format="DD-MM-YYYY") as writer:
                    sheets_data = {"Data_Clean": df_final, "Error_Tanpa_Kode_Unit": df_tanpa_kode, "Error_Tanpa_Tgl_Lahir": df_tanpa_tgl}
                    
                    for s_name, dframe in sheets_data.items():
                        if not dframe.empty: dframe.to_excel(writer, sheet_name=s_name, index=False)
                    
                    wb = writer.book
                    if "Data_Clean" in wb.sheetnames:
                        ws = wb["Data_Clean"]
                        for col in ws.iter_cols(min_row=2):
                            c_name = ws.cell(row=1, column=col[0].column).value
                            t_aturan = target_to_tipe.get(c_name, "Teks") if c_name != "no" else "Angka"
                            if t_aturan == "Tanggal (DD-MM-YYYY)":
                                for cell in col:
                                    if cell.value: cell.number_format = "DD-MM-YYYY"
                            elif t_aturan == "Angka":
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
                
                # HASIL
                st.success("✨ Konsolidasi berhasil!")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Pegawai Terstruktur", f"{len(df_final):,} Baris".replace(",", "."))
                col2.metric("Fasyankes Tanpa Kode", f"{len(df_tanpa_kode)} Unit")
                col3.metric("Pegawai Tanpa Tgl Lahir", f"{len(df_tanpa_tgl)} Orang")
                
                st.markdown("---")
                st.download_button("📥 Unduh File Excel Profesional", data=output_buffer, file_name="Data_Pegawai_Final_DIY.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

            except Exception as e:
                st.error(f"❌ Terjadi kesalahan teknis: {e}")

import streamlit as st
import pandas as pd
import io
import os

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Aplikasi Rekap Data SDMK Fasyankes DIY",
    page_icon="🏥",
    layout="wide"
)

st.title("🚀 Aplikasi Rekap Data SDMK Fasyankes & Quality Control")
st.markdown("---")

# Sidebar untuk Panduan & Upload File
st.sidebar.header("📁 1. Unggah Berkas Sumber")
uploaded_files = st.sidebar.file_uploader(
    "Pilih file laporan (.xls / .html)", 
    type=["xls", "html"], 
    accept_multiple_files=True
)

master_file = st.sidebar.file_uploader(
    "Pilih file Master Fasyankes (.xlsx)", 
    type=["xlsx"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Panduan Singkat:**\n"
    "1. Upload satu atau banyak file laporan fasyankes.\n"
    "2. Upload file master fasyankes baku.\n"
    "3. Klik tombol proses di bawah.\n"
    "4. Download hasil file bersih & laporan error."
)

if st.button("🔄 GABUNGKAN & PROSES DATA SEKARANG", type="primary", use_container_width=True):
    if not uploaded_files or not master_file:
        st.error("⚠️ Harap unggah minimal satu file laporan dan file Master Fasyankes terlebih dahulu!")
    else:
        with st.spinner("Sedang memproses konsolidasi data dan pemeriksaan kualitas..."):
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
                            # Deteksi header baris pertama jika berupa tabel fasyankes
                            if "No" in str(df.iloc[0, 0]) or "Nama Fasyankes" in str(df.iloc[0, 1]):
                                df.columns = df.iloc[0]
                                df = df[1:].reset_index(drop=True)
                            data_frames.append(df)
                    except Exception as e:
                        st.warning(f"Gagal membaca {uploaded_file.name}: {e}")

                if not data_frames:
                    st.error("Tidak ada data valid yang berhasil diekstrak dari file laporan.")
                else:
                    df_raw = pd.concat(data_frames, ignore_index=True)

                    # 2. Membaca Master Fasyankes
                    df_master = pd.read_excel(master_file)

                    # 3. Normalisasi & Joining Aman (Anti Spasi & Case Insensitive)
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

                        # Rewrite Nama Fasyankes dengan nama baku Master
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

                    # 5. Mapping Kolom Sesuai Standar Target
                    mapping_config = [
                        ("Master Fasyankes", "Kode", "kode_unit", "Teks Bersih"),
                        ("Laporan Fasyankes", "Nama Fasyankes", "nama_unit", "Teks"),
                        ("Laporan Fasyankes", "NIK", "nik", "Teks Bersih"),
                        ("Laporan Fasyankes", "Tanggal Lahir", "tanggal_lahir", "Tanggal (DD-MM-YYYY)"),
                        ("Laporan Fasyankes", "Nama Lengkap", "nama", "Teks"),
                        ("Laporan Fasyankes", "Jenis Tenaga", "jenis_tenaga", "Teks"),
                        ("Laporan Fasyankes", "Status", "status_pegawai", "Teks"),
                        ("Laporan Fasyankes", "Jenis Kelamin", "jenis_kelamin", "Teks"),
                        ("Laporan Fasyankes", "Nomor STR", "nomor_str", "Teks Bersih"),
                        ("Laporan Fasyankes", "Status STR", "status_str", "Teks"),
                        ("Laporan Fasyankes", "Nomor SIP", "nomor_sip", "Teks Bersih"),
                        ("Laporan Fasyankes", "Tanggal Terbit SIP", "tanggal_terbit_sip", "Tanggal (DD-MM-YYYY)"),
                        ("Laporan Fasyankes", "Tanggal Berakhir SIP", "tanggal_berakhir_sip", "Tanggal (DD-MM-YYYY)"),
                    ]

                    df_final = pd.DataFrame()
                    df_final["no"] = range(1, len(df_merged) + 1)
                    target_to_tipe = {}

                    for _, _, target, tipe in mapping_config:
                        target_to_tipe[target] = tipe

                    for _, asal, target, tipe in mapping_config:
                        if asal in df_merged.columns:
                            if tipe == "Tanggal (DD-MM-YYYY)":
                                df_final[target] = pd.to_datetime(df_merged[asal], errors="coerce")
                            elif tipe == "Angka":
                                df_final[target] = pd.to_numeric(df_merged[asal], errors="coerce")
                            else:
                                df_final[target] = df_merged[asal].apply(force_string)
                        else:
                            df_final[target] = None

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

                    # 7. Generate Excel ke Memory Buffer
                    output_buffer = io.BytesIO()
                    with pd.ExcelWriter(
                        output_buffer,
                        engine="openpyxl",
                        date_format="DD-MM-YYYY",
                        datetime_format="DD-MM-YYYY",
                    ) as writer:
                        df_final.to_excel(writer, sheet_name="Data_Clean", index=False)
                        worksheet = writer.sheets["Data_Clean"]

                        # Format sel openpyxl aman
                        for col in worksheet.iter_cols(min_row=2):
                            col_name = worksheet.cell(row=1, column=col[0].column).value
                            tipe_aturan = target_to_tipe.get(col_name, "Teks") if col_name != "no" else "Angka"

                            if tipe_aturan == "Tanggal (DD-MM-YYYY)":
                                for cell in col:
                                    if cell.value is not None:
                                        cell.number_format = "DD-MM-YYYY"
                            elif tipe_aturan == "Angka":
                                for cell in col:
                                    if cell.value is not None:
                                        cell.number_format = "0"
                            else:
                                for cell in col:
                                    if cell.value is not None:
                                        cell.number_format = '@'

                        if not df_tanpa_kode.empty:
                            df_tanpa_kode.to_excel(writer, sheet_name="Error_Tanpa_Kode_Unit", index=False)
                        if not df_tanpa_tgl.empty:
                            df_tanpa_tgl.to_excel(writer, sheet_name="Error_Tanpa_Tgl_Lahir", index=False)

                    output_buffer.seek(0)

                    # Tampilan Sukses & Tombol Download
                    st.success("🎉 Konsolidasi dan Analisis Kualitas Data Berhasil Diselesaikan!")
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Total Data Pegawai Bersih", f"{len(df_final)} Baris")
                    col2.metric("Fasyankes Tanpa Kode Unit", f"{len(df_tanpa_kode)} Fasyankes")

                    st.download_button(
                        label="📥 Download File Hasil Final (Data_Pegawai_Final.xlsx)",
                        data=output_buffer,
                        file_name="Data_Pegawai_Final.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"Terjadi kesalahan sistem saat memproses data: {e}")
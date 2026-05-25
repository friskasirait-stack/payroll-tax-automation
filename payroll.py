import gspread
import pandas as pd
from fpdf import FPDF
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- KONFIGURASI SISTEM ---
EMAIL_PENGIRIM = "YOUR EMAIL HERE" 
PASSWORD_APP = "MASUKKAN_16_DIGIT_APP_PASSWORD_DISINI" # Ganti dengan App Password-mu

# DYNAMIC PARAMETERIZATION: Simulasi Master Config P3B / Tax Treaty
CONFIG_TARIF_NEGARA = {
    'US': 0.10, 
    'SG': 0.15, 
    'JP': 0.10, 
    'DEFAULT_WNA': 0.20 
}

def hitung_pajak(gaji_bruto, status, warganegara):
    """Logika Pajak Hybrid: WNI (PPh 21 TER) vs WNA (PPh 26 / Tax Treaty)"""
    if warganegara != 'ID':
        tarif = CONFIG_TARIF_NEGARA.get(warganegara, CONFIG_TARIF_NEGARA['DEFAULT_WNA'])
        return int(gaji_bruto * tarif), f"PPh 26 / P3B ({int(tarif*100)}%)"

    kategori_A = ['TK/0', 'TK/1', 'K/0']
    kategori_B = ['TK/2', 'TK/3', 'K/1', 'K/2']
    kategori_C = ['K/3']
    
    tarif = 0
    if status in kategori_A:
        if gaji_bruto <= 5400000: tarif = 0
        elif gaji_bruto <= 10000000: tarif = 0.02
        else: tarif = 0.04
    elif status in kategori_B:
        if gaji_bruto <= 6200000: tarif = 0
        elif gaji_bruto <= 10000000: tarif = 0.015
        else: tarif = 0.03
    elif status in kategori_C:
        if gaji_bruto <= 6600000: tarif = 0
        elif gaji_bruto <= 10000000: tarif = 0.0125
        else: tarif = 0.02
        
    return int(gaji_bruto * tarif), "PPh 21 (TER)"

def generate_slip_gaji(row):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="PAYROLL PORTFOLIO", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(100, 100, 100) 
    pdf.cell(0, 8, txt="SLIP GAJI KARYAWAN", ln=True, align='C')
    
    pdf.set_draw_color(50, 50, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(40, 8, txt="Nama Karyawan", ln=0)
    pdf.cell(5, 8, txt=":", ln=0)
    pdf.cell(100, 8, txt=f"{row['Nama']}", ln=1)
    
    pdf.cell(40, 8, txt="Kewarganegaraan", ln=0)
    pdf.cell(5, 8, txt=":", ln=0)
    pdf.cell(100, 8, txt=f"{row['Kewarganegaraan']} (Status: {row['Status']})", ln=1)
    
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(230, 230, 230) 
    pdf.cell(100, 10, txt="  Keterangan", border=1, fill=True, ln=0)
    pdf.cell(90, 10, txt="Jumlah (Rp)  ", border=1, fill=True, ln=1, align='R')
    
    pdf.set_font("Arial", size=11)
    pdf.cell(100, 8, txt="  Gaji Pokok", border='LR', ln=0)
    pdf.cell(90, 8, txt=f"{row['Gaji Pokok']:,.0f}".replace(',', '.'), border='LR', ln=1, align='R')
    
    pdf.cell(100, 8, txt="  Tunjangan", border='LR', ln=0)
    pdf.cell(90, 8, txt=f"{row['Tunjangan']:,.0f}".replace(',', '.'), border='LR', ln=1, align='R')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 8, txt="  Total Gaji Bruto", border='LR', ln=0)
    pdf.cell(90, 8, txt=f"{row['Gaji Bruto']:,.0f}".replace(',', '.'), border='LR', ln=1, align='R')
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(100, 8, txt=f"  Potongan {row['Jenis Pajak']}", border='LR', ln=0)
    pdf.cell(90, 8, txt=f"- {row['Potongan Pajak']:,.0f}".replace(',', '.'), border='LR', ln=1, align='R')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(210, 235, 255) 
    pdf.cell(100, 12, txt="  GAJI BERSIH DITERIMA", border=1, fill=True, ln=0)
    pdf.cell(90, 12, txt=f"{row['Gaji Bersih']:,.0f}".replace(',', '.'), border=1, fill=True, ln=1, align='R')
    
    if not os.path.exists('slip_gaji'):
        os.makedirs('slip_gaji')
        
    nama_file = f"slip_gaji/Slip_{row['Nama']}.pdf"
    pdf.output(nama_file)
    return nama_file

def kirim_email(nama, email_tujuan, file_pdf):
    msg = EmailMessage()
    msg['Subject'] = f"Dokumen Rahasia: Slip Gaji Bulan Ini - {nama}"
    msg['From'] = EMAIL_PENGIRIM
    msg['To'] = email_tujuan
    msg.set_content(f"Halo {nama},\n\nBerikut terlampir slip gaji Anda dari sistem Payroll Portfolio.\nDokumen ini bersifat rahasia.\n\nSalam,\nTim Finance")
    
    with open(file_pdf, 'rb') as f:
        pdf_data = f.read()
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(file_pdf))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_PENGIRIM, PASSWORD_APP)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"  -> Gagal mengirim email ke {nama}: {e}")
        return False

def process_payroll_enterprise():
    print("Memulai Enterprise ETL Pipeline (Row-Level Audit Trail)...")

    # 1. EXTRACT & CLEANING
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open('Payroll_Portofolio').sheet1 
    df = pd.DataFrame(sh.get_all_records())
    
    jml_awal = len(df)
    df = df.drop_duplicates(subset=['Nama'], keep='first')
    jml_akhir = len(df)
    print(f"Data Cleaning: Mendeteksi {jml_awal} baris. Tersisa {jml_akhir} data unik setelah deduplikasi.")
    
    # 2. TRANSFORM (Kalkulasi)
    df['Gaji Pokok'] = pd.to_numeric(df['Gaji Pokok'])
    df['Tunjangan'] = pd.to_numeric(df['Tunjangan'])
    df['Gaji Bruto'] = df['Gaji Pokok'] + df['Tunjangan']
    
    hasil_pajak = df.apply(lambda row: hitung_pajak(row['Gaji Bruto'], row['Status'], row['Kewarganegaraan']), axis=1)
    df['Potongan Pajak'] = [x[0] for x in hasil_pajak]
    df['Jenis Pajak'] = [x[1] for x in hasil_pajak]
    df['Gaji Bersih'] = df['Gaji Bruto'] - df['Potongan Pajak']
    
    # Menyiapkan list penampung untuk System Logs per baris
    status_logs = []
    timestamps = []
    
    # 3. GENERATE PDF & EMAIL (Sambil mencatat status log)
    print("\nMembuat file PDF, mengirim email, dan mencatat Log Audit...")
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_terkirim = 0
    
    for index, row in df.iterrows():
        file_pdf = generate_slip_gaji(row)
        status_baris = "SUCCESS - PDF Generated"
        
        # Logika Pengiriman Email
        if pd.notna(row['Email']) and row['Email'] != "":
            if "@gmail.com" in row['Email']: 
                berhasil = kirim_email(row['Nama'], row['Email'], file_pdf)
                if berhasil:
                    email_terkirim += 1
                    status_baris = "SUCCESS - Email Sent"
                else:
                    status_baris = "FAILED - Email Error"
            else:
                status_baris = "SUCCESS - Skip Dummy Email"
                
        status_logs.append(status_baris)
        timestamps.append(waktu_sekarang)
        
    # Memasukkan array log ke dalam dataframe utama
    df['Timestamp Eksekusi'] = timestamps
    df['Status Sistem'] = status_logs
    
    # Buang kolom helper 'Jenis Pajak' agar tampilan sheets tidak terlalu berantakan
    df_load = df.drop(columns=['Jenis Pajak'])
    
    # 4. LOAD (Update seluruh Google Sheets sekaligus)
    sh.clear()
    sh.update([df_load.columns.values.tolist()] + df_load.values.tolist())
    print(f"\nSelesai! {email_terkirim} email terkirim. Status Sistem dan Timestamp telah ditambahkan di sebelah kolom Gaji Bersih.")

if __name__ == "__main__":
    process_payroll_enterprise()
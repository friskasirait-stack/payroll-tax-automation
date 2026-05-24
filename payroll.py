import gspread
import pandas as pd
from fpdf import FPDF
import os
import smtplib
from email.message import EmailMessage

# --- KONFIGURASI EMAIL ---
EMAIL_PENGIRIM = "YOUR EMAIL" 
PASSWORD_APP = "YOUR PASSWORD"  # Ganti dengan 16 digit App Password kamu

def hitung_pph21_ter(gaji_bruto, status):
    """Logika TER PPh 21 berdasarkan kategori status PTKP"""
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
        
    return int(gaji_bruto * tarif)

def generate_slip_gaji(row):
    """Generate PDF Slip Gaji per Karyawan dengan desain Estetik dan Rapi"""
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER PERUSAHAAN ---
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="PAYROLL PORTFOLIO", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(100, 100, 100) 
    pdf.cell(0, 8, txt="SLIP GAJI KARYAWAN", ln=True, align='C')
    
    # Garis pembatas dinamis
    pdf.set_draw_color(50, 50, 50)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(10)
    
    # --- IDENTITAS KARYAWAN ---
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(40, 8, txt="Nama Karyawan", ln=0)
    pdf.cell(5, 8, txt=":", ln=0)
    pdf.cell(100, 8, txt=f"{row['Nama']}", ln=1)
    
    pdf.cell(40, 8, txt="Status PTKP", ln=0)
    pdf.cell(5, 8, txt=":", ln=0)
    pdf.cell(100, 8, txt=f"{row['Status']}", ln=1)
    
    pdf.ln(5)
    
    # --- HEADER TABEL RINCIAN ---
    pdf.set_font("Arial", 'B', 11)
    pdf.set_fill_color(230, 230, 230) 
    pdf.cell(100, 10, txt="  Keterangan", border=1, fill=True, ln=0)
    pdf.cell(90, 10, txt="Jumlah (Rp)  ", border=1, fill=True, ln=1, align='R')
    
    # --- ISI TABEL RINCIAN ---
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
    pdf.cell(100, 8, txt="  Potongan PPh 21 (TER)", border='LR', ln=0)
    pdf.cell(90, 8, txt=f"- {row['Potongan Pajak']:,.0f}".replace(',', '.'), border='LR', ln=1, align='R')
    
    # --- GAJI BERSIH (FOOTER TABEL) ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(210, 235, 255) 
    pdf.cell(100, 12, txt="  GAJI BERSIH DITERIMA", border=1, fill=True, ln=0)
    pdf.cell(90, 12, txt=f"{row['Gaji Bersih']:,.0f}".replace(',', '.'), border=1, fill=True, ln=1, align='R')
    
    # Simpan file
    if not os.path.exists('slip_gaji'):
        os.makedirs('slip_gaji')
        
    nama_file = f"slip_gaji/Slip_{row['Nama']}.pdf"
    pdf.output(nama_file)
    return nama_file

def kirim_email(nama, email_tujuan, file_pdf):
    """Kirim PDF ke email masing-masing karyawan"""
    msg = EmailMessage()
    msg['Subject'] = f"Dokumen Rahasia: Slip Gaji Bulan Ini - {nama}"
    msg['From'] = EMAIL_PENGIRIM
    msg['To'] = email_tujuan
    msg.set_content(f"Halo {nama},\n\nBerikut terlampir slip gaji Anda dari Payroll Portfolio.\nDokumen ini bersifat rahasia.\n\nSalam,\nTim Finance")
    
    with open(file_pdf, 'rb') as f:
        pdf_data = f.read()
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=os.path.basename(file_pdf))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_PENGIRIM, PASSWORD_APP)
            smtp.send_message(msg)
        print(f"  -> Email sukses terkirim ke {nama} ({email_tujuan})")
    except Exception as e:
        print(f"  -> Gagal mengirim email ke {nama}: {e}")

def process_payroll_and_generate_slips():
    print("Memulai pipeline Payroll Portfolio...")

    # 1. EXTRACT & CLEANING
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open('Payroll_Portofolio').sheet1 
    df = pd.DataFrame(sh.get_all_records())
    
    jml_awal = len(df)
    df = df.drop_duplicates(subset=['Nama'], keep='first')
    jml_akhir = len(df)
    print(f"Data Cleaning: Ditemukan {jml_awal - jml_akhir} data duplikat. Telah dibersihkan.")
    
    # 2. TRANSFORM
    df['Gaji Pokok'] = pd.to_numeric(df['Gaji Pokok'])
    df['Tunjangan'] = pd.to_numeric(df['Tunjangan'])
    df['Gaji Bruto'] = df['Gaji Pokok'] + df['Tunjangan']
    df['Potongan Pajak'] = df.apply(lambda row: hitung_pph21_ter(row['Gaji Bruto'], row['Status']), axis=1)
    df['Gaji Bersih'] = df['Gaji Bruto'] - df['Potongan Pajak']
    
    # 3. LOAD
    sh.clear()
    sh.update([df.columns.values.tolist()] + df.values.tolist())
    print("Data yang sudah terverifikasi telah diperbarui di Google Sheets.")
    
    # 4. GENERATE PDF & AUTOMASI EMAIL
    print("\nMembuat file PDF dan mengirim email otomatis...")
    for index, row in df.iterrows():
        file_pdf = generate_slip_gaji(row)
        
        if pd.notna(row['Email']) and row['Email'] != "":
            if "@gmail.com" in row['Email']: 
                kirim_email(row['Nama'], row['Email'], file_pdf)
            else:
                print(f"  -> Melewati pengiriman ke {row['Nama']} (email dummy: {row['Email']})")
                
    print("\nSeluruh pipeline ETL selesai dieksekusi dengan sukses!")

if __name__ == "__main__":
    process_payroll_and_generate_slips()
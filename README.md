# Automated Tax & Payroll Pipeline

## Overview
A Python-based ETL (Extract, Transform, Load) pipeline designed to automate payroll processing, ensure tax compliance, and securely distribute payslips. This project bridges data engineering workflows with Indonesian tax regulations (PPh 21 - TER).

## The Problem It Solves
Manual payroll processing using standard spreadsheets is prone to human error, data duplication, and time-consuming distribution. This system automates the entire workflow from raw data extraction to final document delivery.

## Key Features
* **Data Cleansing:** Automatically detects and removes duplicate employee entries before processing.
* **Tax Compliance Engine:** Calculates deductions based on the latest Indonesian Effective Average Rate (TER PPh 21) categorized by PTKP status.
* **Automated Document Generation:** Creates structured and formatted PDF payslips for each employee.
* **Secure Distribution:** Distributes confidential payslips directly to employees' inboxes via SMTP integration.

## Tech Stack
* **Language:** Python 3
* **Data Handling:** Pandas
* **API Integration:** Google Sheets API (gspread)
* **Document Generation:** FPDF
* **Automation:** smtplib, email.message

## How to Run
1. Clone this repository.
2. Install dependencies: `pip install pandas gspread fpdf`
3. Add your `credentials.json` for Google Sheets API access.
4. Run `python payroll_pro.py` in your terminal.
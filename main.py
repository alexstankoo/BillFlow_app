from fastapi import FastAPI
from fastapi.responses import FileResponse
from fpdf import FPDF
import os

app = FastAPI()

@app.get("/")
def get_root():
    """
    Root endpoint to verify if the API is running.
    """
    return {"status": "success", "message": "BillFlow Backend API is operational."}

@app.get("/generate-invoice")
def generate_invoice():
    """
    Generates a sample PDF invoice and returns it as a downloadable file.
    """
    # 1. Initialize PDF document
    pdf_document = FPDF()
    pdf_document.add_page()
    
    # 2. Set header font (Arial, Bold, 16)
    pdf_document.set_font("Arial", "B", 16)
    
    # 3. Add invoice title
    pdf_document.cell(40, 10, "INVOICE - BillFlow")
    pdf_document.ln(10) # Line break
    
    # 4. Add invoice details with regular font
    pdf_document.set_font("Arial", "", 12)
    pdf_document.cell(40, 10, "Customer: John Doe")
    pdf_document.ln(8)
    pdf_document.cell(40, 10, "Amount: 50.00 EUR")
    pdf_document.ln(8)
    pdf_document.cell(40, 10, "Service: PC Repair and Maintenance")

    # 5. Define output path and save the file
    output_filename = "invoice_sample.pdf"
    pdf_document.output(output_filename)

    # 6. Return the generated file as a response
    return FileResponse(
        path=output_filename, 
        media_type='application/pdf', 
        filename="invoice_billflow.pdf"
    )
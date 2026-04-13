from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fpdf import FPDF
from typing import List

app = FastAPI()

# --- PYDANTIC MODELS (SECURITY GUARDS) ---

# 1. Create a new model for a SINGLE item on the quote
class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float

# 2. Update the main request to hold a LIST of those items
class QuoteRequest(BaseModel):
    customer_name: str
    currency: str = "EUR" # Setting a default value
    items: List[LineItem] # This tells FastAPI to expect an array of items


# --- PDF GENERATION ENGINE ---

def create_pdf_layout(data: QuoteRequest):
    """
    Generates a PDF with a dynamic table of line items and calculates DPH.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Register Roboto fonts (Requires Roboto-Regular.ttf and Roboto-Bold.ttf in root folder)
    pdf.add_font("Roboto", "", "Roboto-Regular.ttf")
    pdf.add_font("Roboto", "B", "Roboto-Bold.ttf")
    
    # --- HEADER ---
    pdf.set_font("Roboto", "B", 20)
    pdf.cell(0, 15, "CENOVÁ PONUKA", ln=True, align='C')
    pdf.ln(5)
    
    # --- CUSTOMER INFO ---
    pdf.set_font("Roboto", "B", 12)
    pdf.cell(0, 10, f"Zákazník: {data.customer_name}", ln=True)
    pdf.ln(5)
    
    # --- TABLE HEADER ---
    pdf.set_font("Roboto", "B", 12)
    pdf.cell(90, 10, "Popis služby", border=1)
    pdf.cell(30, 10, "Množstvo", border=1, align='C')
    pdf.cell(35, 10, "Cena/ks", border=1, align='C')
    pdf.cell(35, 10, "Spolu", border=1, align='C')
    pdf.ln(10)
    
    # --- TABLE ROWS & MATH ---
    pdf.set_font("Roboto", "", 12)
    subtotal = 0.0
    
    # Loop through every item the user sent us
    for item in data.items:
        # Calculate math for this specific row
        line_total = item.quantity * item.unit_price
        subtotal += line_total
        
        # Draw the row cells
        pdf.cell(90, 10, item.description, border=1)
        pdf.cell(30, 10, str(item.quantity), border=1, align='C')
        pdf.cell(35, 10, f"{item.unit_price:.2f}", border=1, align='C')
        pdf.cell(35, 10, f"{line_total:.2f}", border=1, align='C')
        pdf.ln(10)
        
    # --- TOTALS & DPH (VAT) ---
    pdf.ln(5)
    tax_rate = 0.20  # 20% DPH
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount
    
    pdf.set_font("Roboto", "B", 12)
    pdf.cell(0, 8, f"Základ dane: {subtotal:.2f} {data.currency}", ln=True, align='R')
    pdf.cell(0, 8, f"DPH (20%): {tax_amount:.2f} {data.currency}", ln=True, align='R')
    
    pdf.set_font("Roboto", "B", 14)
    pdf.cell(0, 12, f"Celkom k úhrade: {grand_total:.2f} {data.currency}", ln=True, align='R')
    
    # --- SAVE FILE ---
    file_path = "quote_output.pdf"
    pdf.output(file_path)
    return file_path


# --- API ENDPOINTS ---

@app.post("/generate-quote")
def generate_quote(request: QuoteRequest):
    """
    Endpoint that accepts JSON payload, triggers the PDF generation, 
    and returns the physical file to the user.
    """
    # 1. Trigger the layout function with the incoming data
    generated_file = create_pdf_layout(request)
    
    # 2. Return the generated file back to the client
    return FileResponse(
        path=generated_file, 
        fshorilename="cenova_ponuka.pdf", 
        media_type="application/pdf"
    )
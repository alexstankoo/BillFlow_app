from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
import google.generativeai as genai
import json
import os
from jinja2 import Environment, FileSystemLoader

genai.configure(api_key = "")
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI(title = "BillFlow AI")

#pydantic models for the quote
class Item(BaseModel):
    name: str = Field(..., description = "First Service Name")
    quantity: int = Field(default=1, description="Number of Pieces")
    unit_price: Optional[float] = Field(default=None, description = "Price per unit in EUR")
    type_of_unit: Optional[str] = Field(default=None, description = "Name of the unit")
    vat_percentage: float = Field(default = 20.0, description = "vat percentage")

    @computed_field
    def total_item_price(self) -> float:
        if self.unit_price is not None:
            return self.quantity * self.unit_price
        return 0.0
    
    @computed_field
    def vat_amount(self) -> float:
        return self.total_item_price * (self.vat_percentage / 100)

    @computed_field
    def price_with_vat(self) -> float:
        return self.total_item_price + self.vat_amount

class QuoteData(BaseModel):
    client_name: str = Field(default = "Unknown client")
    project_name: Optional[str] = Field(default = None)
    items: List[Item] = Field(default_factory=list)
    
    @computed_field
    def total_netto(self) -> float:
        total = 0.0
        for item in self.items:
            if item.unit_price is not None:
                subtotal = item.unit_price * item.quantity
                total += subtotal
            else:
                total += 0.0
        return total
    
    @computed_field
    def total_brutto(self) -> float:
        total = 0.0
        for item in self.items:
            total += item.price_with_vat 
        return total

class TextInput(BaseModel):
    text: str = Field(..., description = "Raw text input")

@app.post("/api/generate-quote")
async def process_and_generate(data: TextInput):
    prompt = f"""
    Extract billing information from the provided text and transform it into a structured JSON object.

    ### RULES:
    1. Return ONLY raw JSON. No markdown (```), no backticks, no conversational text.
    2. For each item, look for: name, quantity, unit price, unit type (m2, hrs, pcs, etc.), and VAT rate.
    3. If unit_price is missing, set it to null.
    4. If vat_percentage is not explicitly mentioned for an item, use the default value provided below.
    5. Ensure all numerical values are floats or integers, not strings.

    ### JSON STRUCTURE:
    {{
        "client_name": "Full name of the client or company",
        "project_name": "Title of the quote or project",
        "items": [
            {{
                "name": "Clear description of the service or product",
                "quantity": 1,
                "unit_price": 15.5,
                "type_of_unit": "pcs",
                "vat_percentage": 20.0
            }}
        ]
    }}

    ### CONTEXT:
    - Default VAT: 20.0%
    - Currency: EUR

    Text to process:
    {data.text}
    """

    try:
        response = model.generate_content(prompt)
        raw_json = response.text.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(raw_json)
        quote = QuoteData(**ai_data)
    except Exception as error:
        raise HTTPException(status_code = 400, detail = f"Ai returned invalid format {str(error)}")
    
    missing_prices = []
    for i in quote.items:
        if i.unit_price is None:
            missing_prices.append(i.name)

    if missing_prices:
        warning_msg = f"Missing prices: {missing_prices}"
    else:
        warning_msg = "Data complete."

    return {
        "status": "success",
        "warning": warning_msg,
        "results": {
            "client": quote.client_name,
            "project": quote.project_name,
            "summary": {
                "total_net": quote.total_netto,
                "total_brutto": quote.total_brutto,
                "total_vat": quote.total_brutto - quote.total_netto
            },
            "billing_details": quote.model_dump()
        }
    }
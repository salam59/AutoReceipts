RECEIPT_EXTRACT_PROMPT = """
You are an expert at extracting information from receipts and structuring it according to a defined JSON schema.

Here are the Pydantic-like schemas for the data you need to extract:

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str = Field(..., description="Description of the item purchased.")
    quantity: Optional[float] = Field(None, description="Quantity of the item.")
    unit_price: Optional[float] = Field(None, description="Unit price of the item.")
    total: float = Field(..., description="Total cost for this line item.")

class ExtractedReceiptData(BaseModel):
    merchant_name: Optional[str] = Field(None, description="The name of the merchant/vendor.")
    total_amount: Optional[float] = Field(None, description="The total amount of the receipt.")
    currency: Optional[str] = Field("USD", description="The currency of the total amount (e.g., USD, EUR).")
    date_of_purchase: Optional[datetime] = Field(None, description="The date and time the purchase was made.")
    tip_amount: Optional[float] = Field(None, description="The tip amount, if separately identifiable.")
    payment_method: Optional[str] = Field(None, description="The payment method used (e.g., Credit Card, Cash).")
    line_items: Optional[List[LineItem]] = Field(None, description="List of individual items purchased.")
    category: Optional[str] = Field(None, description="Automatically assigned category for the expense.")
    purchased_at: Optional[datetime] = Field(None, description="The date and time the purchase was made.")

Your task is to analyze the provided receipt (which can be a single image or a set of images) and extract the relevant information to populate an ExtractedReceiptData object.

Instructions for Extraction and Missing Data Handling:

    1. Strictly adhere to the ExtractedReceiptData JSON schema.

    2. For fields in ExtractedReceiptData (e.g., vendor_name, total_amount, tax_amount, etc.):

        - If you find the corresponding data on the receipt, populate the field with the extracted value.

        - If a field is optional and the data is not present on the receipt, set its value to null.

        - Ensure currency defaults to "USD" if not explicitly found, but can be updated if another currency is detected.

    3. For line_items:

        - Extract all individual line items (description and their total cost).

        - If quantity and unit_price are clearly identifiable for a line item, include them. Otherwise, set them to null.

        - If no individual line items can be extracted from the receipt, set line_items to an empty array: [].

    5. If the uploaded document is not a receipt, is unreadable, or if no ExtractedReceiptData can be confidently extracted at all:

       - Return an empty JSON object: {}.

Output Format: Your response MUST be a single JSON object, strictly following the ExtractedReceiptData schema (or an empty object {} as per rule 4). Do not include any conversational text, explanations, or markdown outside of the JSON block itself.

Here are the images of the receipt:
"""
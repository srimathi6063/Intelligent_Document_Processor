import boto3
import json
import os
import re
from botocore.config import Config

# Set your AWS region here or via environment variable AWS_REGION
REGION = os.getenv("AWS_REGION", "us-east-1")

# Configure Bedrock client with extended timeouts
try:
    from config.settings import settings
    bedrock_config = Config(
        read_timeout=settings.BEDROCK_READ_TIMEOUT,
        connect_timeout=settings.BEDROCK_CONNECT_TIMEOUT,
        retries={'max_attempts': settings.BEDROCK_MAX_RETRIES}
    )
except ImportError:
    # Fallback configuration if settings not available
    bedrock_config = Config(
        read_timeout=300,      # 5 minutes for read timeout
        connect_timeout=60,    # 1 minute for connection timeout
        retries={'max_attempts': 3}  # Retry up to 3 times
    )

bedrock = boto3.client('bedrock-runtime', region_name=REGION, config=bedrock_config)

def call_bedrock_llm(extracted_text):
    print(f"🤖 [LLM EXTRACTION] Starting LLM extraction process...")
    print(f"📏 [LLM EXTRACTION] Input text length: {len(extracted_text)} characters")
    print(f"📝 [LLM EXTRACTION] Input text preview (first 300 chars): {extracted_text[:300]}...")
    
    prompt = f"""
You are an expert AI specialized in extracting structured data from diverse financial documents such as invoices or purchase orders.

Note that different documents may use different terms or formats for similar fields.

Your Goal:
Extract all **explicitly mentioned** information from the given invoice or purchase order text and return a structured JSON. Do not guess or infer missing fields.

**Billing Details:**
- "billing_organization_name": Billed by, Vendor, From, Company Name
- "billing_address": Bill To, Billing Address, Supplier Address, Invoice Address
- "billing_contact_information": contact details, emails, names, etc.
- "billing_phone_number": contact phone of billing party
- "billing_gst_number": GSTIN, GST Number of billing party
- "billing_hsn_number": HSN Code or SAC Code mentioned near billing items

**Shipping Details:**
- "shipping_organization_name": Shipped to, Consignee, Delivery Party, Supplier
- "shipping_address": Ship To, Shipping Address, Delivery Address
- "shipping_contact_information": contact details, emails, names, etc.
- "shipping_phone_number": contact phone of shipping party
- "shipping_gst_number": GSTIN, GST Number of shipping party
- "shipping_hsn_number": HSN Code or SAC Code mentioned near shipping details

# Do not use the following values as organization names:
# Uniware Systems, Uniware Systems (P) Ltd, UNIWARE SYSTEMS (P) LTD, Uniware Systems Pvt. Ltd, Uniware Systems Pvt. Ltd., UNIWARE SYSTEMS PVT LTD

**Document Identifiers:**
- "invoice_number": invoice no, document no, inv #
- "invoice_date": invoice date, issue date, billing date
- "due_date": due date, payment due
- "po_number": purchase order, PO #, order number
- "payment_terms": net 30, due in 15 days, etc.
- "delivery_date": delivery or expected shipping date
- "terms_conditions": any terms, policies, or legal clauses
- "notes": special instructions or remarks

**Financial Summary:**
- "currency": extract ₹, $, €, or currency code
- "subtotal": amount before tax or discount
- "discount": any applied discount
- "tax_amount": sum of GST/CGST/SGST/IGST/VAT/sales tax, etc.
- "total_amount": grand total / final payable

**Line Items:**
Extract details for all items with:
- "S.NO": serial number (starting from 1)
- "description": item/service name
- "quantity": number of units
- "unit_price": per unit cost
- "total_per_product": line total (qty × unit price)

----------------------------------------------------
📌 Data Extraction Rules:
----------------------------------------------------
1. Do not infer or guess. Mark as "NA" if not present.
2. Extract numeric values only from amounts (no currency symbols).
3. Maintain date formats as-is.
4. Combine multi-line addresses or names into single lines.
5. Sum all tax components into `tax_amount`.
6. Return structured JSON with ALL fields exactly as defined.

----------------------------------------------------
🎯 Output JSON Format:
----------------------------------------------------

{{
    "billing_organization_name": "",
    "billing_address": "",
    "billing_contact_information": "",
    "billing_phone_number": "",
    "billing_gst_number": "",
    "billing_hsn_number": "",
    "shipping_organization_name": "",
    "shipping_address": "",
    "shipping_contact_information": "",
    "shipping_phone_number": "",
    "shipping_gst_number": "",
    "shipping_hsn_number": "",
  "invoice_number": "",
  "invoice_date": "",
  "due_date": "",
  "po_number": "",
  "payment_terms": "",
  "delivery_date": "",
  "currency": "",
  "subtotal": "",
  "discount": "",
  "tax_amount": "",
  "total_amount": "",
  "terms_conditions": "",
  "notes": "",
  "line_items": [
    {{
      "S.NO": 1,
      "description": "",
      "quantity": "",
      "unit_price": "",
      "total_per_product": ""
    }}
  ]
}}

Invoice Text:
{extracted_text}

Respond only with the JSON above and nothing else.
"""
    
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1500,
        "temperature": 0,
        "top_k": 250,
        "top_p": 1.0,
        "stop_sequences": []
    }

    print(f"🤖 [LLM EXTRACTION] Calling Bedrock Claude model (Opus)...")
    print(f"📊 [LLM EXTRACTION] Prompt length: {len(prompt)} characters")
    print(f"🔧 [LLM EXTRACTION] Model: us.anthropic.claude-opus-4-1-20250805-v1:0")
    print(f"⚙️ [LLM EXTRACTION] Parameters: max_tokens=1500, temperature=0")
    
    response = bedrock.invoke_model(
        modelId='us.anthropic.claude-opus-4-1-20250805-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps(body)
    )

    try:
        body_str = response['body'].read().decode()
        result = json.loads(body_str)

        # Debug logs - you can comment these out in production
        print(f"📥 [LLM EXTRACTION] Received response from Bedrock")
        print(f"📋 [LLM EXTRACTION] Response content type: {type(result.get('content'))}")
        print(f"📄 [LLM EXTRACTION] Raw response content: {result.get('content')}")

        content = result.get("content")

        # Handle if content is a list (possibly with dicts or strings)
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    # Try to extract 'text', 'content', or 'message' from dict
                    text_piece = None
                    for key in ("text", "content", "message"):
                        if key in item and isinstance(item[key], str):
                            text_piece = item[key]
                            break
                    if not text_piece:
                        # fallback to json string
                        text_piece = json.dumps(item)
                    parts.append(text_piece)
                else:
                    parts.append(str(item))
            content = " ".join(parts)
        elif not isinstance(content, str):
            content = str(content)

        content = content.strip()

        # Extract JSON portion from content string
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            structured_data = json.loads(json_str)
            print(f"✅ [LLM EXTRACTION] Successfully extracted structured JSON")
            print(f"📊 [LLM EXTRACTION] Extracted fields: {list(structured_data.keys())}")
            print(f"📄 [LLM EXTRACTION] Sample extracted data:")
            for key, value in list(structured_data.items())[:5]:  # Show first 5 fields
                print(f"   {key}: {str(value)[:100]}...")
            return structured_data
        else:
            # fallback: parse entire content as JSON
            print(f"⚠️ [LLM EXTRACTION] No JSON pattern found, trying to parse entire content")
            structured_data = json.loads(content)
            print(f"✅ [LLM EXTRACTION] Fallback parsing successful")
            return structured_data

    except Exception as e:
        print("❌ Bedrock response JSON parse error:", e)
        raise

def call_bedrock_verification(extracted_json, context_text):
    """
    Call AWS Bedrock for verification of extracted data against original text.
    """
    prompt = f"""
You are an expert AI assistant for validating extracted information from invoice or purchase order documents.

Given the extracted JSON data below and the full text of the document, your task is to verify:

- Each field's factual support: Confirm if the data is directly or indirectly supported by the document.
- Identify any unsupported claims: list any fields or values that do not appear or contradict the document.
- Identify contradictions: list any values that contradict information in the document.
- Confirm overall relevance: whether the extracted data is relevant to the document.

Please respond strictly in the following JSON format, matching keys:

{{
  "Supported": "YES" or "NO",
  "Unsupported Claims": [list of field names],
  "Contradictions": [list of field names],
  "Relevant": "YES" or "NO",
  "Additional Details": "Any explanatory notes or observations"
}}

### Extracted JSON:
{json.dumps(extracted_json, indent=2, ensure_ascii=False)}

### Document Text:
{context_text}

Only respond with the JSON above, do NOT include anything else.
"""
    
    try:
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-opus-4-1-20250805-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        verification_text = response_body['content'][0]['text'].strip()
        
        # Parse the verification response
        try:
            # Extract JSON from the response
            start = verification_text.find('{')
            end = verification_text.rfind('}') + 1
            json_part = verification_text[start:end]
            verification_json = json.loads(json_part)
            return verification_json
        except Exception as e:
            # If parsing fails, return a default structure
            return {
                "Supported": "NO",
                "Unsupported Claims": ["Parsing error"],
                "Contradictions": [],
                "Relevant": "NO",
                "Additional Details": f"Failed to parse verification response: {e}"
            }
            
    except Exception as e:
                 return {
             "Supported": "NO",
             "Unsupported Claims": ["API Error"],
             "Contradictions": [],
             "Relevant": "NO",
             "Additional Details": f"Verification API error: {e}"
         }

def call_bedrock_summarization(document_text):
    """
    Call AWS Bedrock for document summarization.
    """
    prompt = f"""
You are an expert AI assistant specialized in creating comprehensive summaries of documents.

Your task is to create a clear, well-structured summary of the provided document text. The summary should:

1. Capture the main points and key information
2. Maintain the logical flow and structure
3. Be concise but comprehensive
4. Use clear, professional language
5. Include important details like dates, names, amounts, and key facts
6. Organize information in a logical manner

Please provide a detailed summary that would be useful for someone who needs to understand the document's content quickly.

Document Text:
{document_text}

Please provide a comprehensive summary of the above document.
"""
    
    try:
        response = bedrock.invoke_model(
            modelId="us.anthropic.claude-opus-4-1-20250805-v1:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response.get('body').read())
        summary_text = response_body['content'][0]['text'].strip()
        
        return summary_text
            
    except Exception as e:
        return f"Error generating summary: {e}"

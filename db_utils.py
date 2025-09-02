


import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool
from config.settings import settings
from utils.logging import logger
from decimal import Decimal, InvalidOperation
import re
import json
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any
import time
from functools import wraps
import os


# Constants
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
POOL_SIZE = 5
CONNECTION_TIMEOUT = 30  # seconds


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class ValidationError(Exception):
    """Custom exception for data validation"""
    pass


# ------------------------------------
# DATE NORMALIZATION: Accepts most common formats --> YYYY-MM-DD
def normalize_date(date_str: str) -> str:
    """Normalize a date string to YYYY-MM-DD, supports common formats."""
    date_str = (date_str or "").strip()
    if not date_str:
        return ""
    patterns = [
        ("%Y-%m-%d", r"^\d{4}-\d{2}-\d{2}$"),
        ("%d-%m-%Y", r"^\d{2}-\d{2}-\d{4}$"),
        ("%d/%m/%Y", r"^\d{2}/\d{2}/\d{4}$"),
        ("%Y/%m/%d", r"^\d{4}/\d{2}/\d{2}$"),
    ]
    for fmt, regex in patterns:
        if re.match(regex, date_str):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    try:
        from dateutil.parser import parse
        dt = parse(date_str, dayfirst=True, yearfirst=False)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return ""


def clean_llm_json_response(response: str) -> str:
    """Clean LLM response to extract valid JSON."""
    if not response:
        return "{}"
    # Remove markdown code blocks ```
    response = re.sub(r"```", "", response)
    json_start = response.find('{')
    if json_start == -1:
        return "{}"
    brace_count = 0
    json_end = -1
    for i, char in enumerate(response[json_start:], json_start):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break
    if json_end == -1:
        return "{}"
    return response[json_start:json_end].strip()


def parse_llm_json_response(response: str) -> Dict[str, Any]:
    """Parse LLM JSON response with error handling and fallback."""
    default_structure = {
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
        "line_items": []
    }
    try:
        cleaned_response = clean_llm_json_response(response)
        parsed_data = json.loads(cleaned_response)
        result = default_structure.copy()
        result.update(parsed_data)
        if not isinstance(result.get("line_items"), list):
            result["line_items"] = []
        cleaned_line_items = []
        for item in result["line_items"]:
            if isinstance(item, dict):
                cleaned_item = {
                    "S.NO": str(item.get("S.NO", "")),
                    "description": str(item.get("description", "")),
                    "quantity": str(item.get("quantity", "")),
                    "unit_price": str(item.get("unit_price", "")),
                    "total_per_product": str(item.get("total_per_product", "")),
                }
                cleaned_line_items.append(cleaned_item)
        result["line_items"] = cleaned_line_items
        for key, value in result.items():
            if key != "line_items" and value is not None:
                result[key] = str(value)
        logger.info("Successfully parsed LLM JSON response")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        logger.error(f"Cleaned response: {cleaned_response[:500]}...")
        try:
            return extract_basic_fields_regex(response)
        except Exception as regex_error:
            logger.error(f"Regex fallback failed: {regex_error}")
            return default_structure
    except Exception as e:
        logger.error(f"Unexpected error parsing LLM response: {e}")
        return default_structure


def extract_basic_fields_regex(text: str) -> Dict[str, Any]:
    """Fallback method to extract basic fields using regex when JSON parsing fails."""
    result = {
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
        "line_items": []
    }

    patterns = {
        "billing_organization_name": r'(?:billing[_\s]?organization[_\s]?name|company[_\s]?name)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "billing_address": r'(?:billing[_\s]?address)["\s]*:?\s*["\']?([^"\'}\n]+)',
        "billing_contact_information": r'(?:billing[_\s]?contact[_\s]?information|billing[_\s]?contact)["\s]*:?\s*["\']?([^"\'}\n]+)',
        "billing_phone_number": r'(?:billing[_\s]?phone[_\s]?number|billing[_\s]?phone)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "billing_gst_number": r'(?:billing[_\s]?gst[_\s]?number|gst[_\s]?number)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "billing_hsn_number": r'(?:billing[_\s]?hsn[_\s]?number|hsn[_\s]?number)["\s]*:?\s*["\']?([^"\'}\n,]+)',

        "shipping_organization_name": r'(?:shipping[_\s]?organization[_\s]?name)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "shipping_address": r'(?:shipping[_\s]?address)["\s]*:?\s*["\']?([^"\'}\n]+)',
        "shipping_contact_information": r'(?:shipping[_\s]?contact[_\s]?information|shipping[_\s]?contact)["\s]*:?\s*["\']?([^"\'}\n]+)',
        "shipping_phone_number": r'(?:shipping[_\s]?phone[_\s]?number|shipping[_\s]?phone)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "shipping_gst_number": r'(?:shipping[_\s]?gst[_\s]?number)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "shipping_hsn_number": r'(?:shipping[_\s]?hsn[_\s]?number)["\s]*:?\s*["\']?([^"\'}\n,]+)',

        "invoice_number": r'(?:invoice[_\s]?number|invoice[_\s]?no|inv[_\s]#)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "invoice_date": r'(?:invoice[_\s]?date|date)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "due_date": r'(?:due[_\s]?date)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "po_number": r'(?:po[_\s]?number|purchase[_\s]?order)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "payment_terms": r'(?:payment[_\s]?terms)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "delivery_date": r'(?:delivery[_\s]?date)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "currency": r'(?:currency)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "subtotal": r'(?:subtotal)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "discount": r'(?:discount)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "tax_amount": r'(?:tax[_\s]?amount)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "total_amount": r'(?:total[_\s]?amount|grand[_\s]?total)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "terms_conditions": r'(?:terms[_\s]?and[_\s]?conditions|terms[_\s]?conditions)["\s]*:?\s*["\']?([^"\'}\n,]+)',
        "notes": r'(?:notes|remarks)["\s]*:?\s*["\']?([^"\'}\n,]+)'
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[field] = match.group(1).strip()

    logger.warning("Used regex fallback for field extraction")
    return result


def validate_date(date_str: str) -> bool:
    """Validates date string format (YYYY-MM-DD)."""
    if not date_str:
        return True
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False



def validate_amount(amount_str: str) -> bool:
    """Validates amount string format."""
    if not amount_str or amount_str.strip().upper() == "NA":
        return False
    try:
        # Remove commas, currency symbols, and whitespace
        cleaned = re.sub(r'[^\d.-]', '', amount_str)
        amount = Decimal(cleaned)
        return amount >= 0
    except (InvalidOperation, ValueError):
        return False



# def validate_amount(amount_str: str) -> str:
#     if not amount_str :
#         return "0"
#     return amount_str





def validate_organization_name(org_name: str) -> bool:
    """Validates organization name."""
    if not org_name or len(org_name.strip()) < 2:
        return False
    pattern = r'^[a-zA-Z0-9\s\-&.,\'()\u00C0-\u017F]+$'
    return bool(re.match(pattern, org_name))


def validate_invoice_number(invoice_num: str) -> bool:
    """Very permissive invoice number validation that only blocks obviously dangerous characters."""
    if not invoice_num or len(invoice_num.strip()) < 1:
        return False
    dangerous_chars = r'[\'\";<>%$]'
    return not re.search(dangerous_chars, invoice_num)


def validate_currency(currency: str) -> bool:
    """Validates currency code."""
    if not currency:
        return True
    valid_currencies = ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY', 'SGD']
    return currency.upper() in valid_currencies


def validate_line_items(line_items: List[Dict]) -> List[Dict]:
    """Validate and clean line items structure."""
    if not isinstance(line_items, list):
        return []
    cleaned_items = []
    for item in line_items:
        if not isinstance(item, dict):
            continue
        cleaned_item = {
            "S.NO": str(item.get("S.NO", "")).strip(),
            "description": str(item.get("description", "")).strip(),
            "quantity": str(item.get("quantity", "1")).strip() or "1",
            "unit_price": str(item.get("unit_price", "0")).strip() or "0",
            "total_per_product": str(item.get("total_per_product", "0")).strip() or "0",
        }
        if cleaned_item["description"]:
            cleaned_items.append(cleaned_item)
    return cleaned_items


class DatabasePool:
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._pool is None:
            try:
                dbconfig = {
                    "host": "13.203.180.36",
                    "database": "Task",
                    "user": "root",
                    "password": "Secure#2024",
                    "port": "3306",
                    "pool_name": "invoice_pool",
                    "pool_size": POOL_SIZE,
                    "pool_reset_session": True,
                    "connect_timeout": CONNECTION_TIMEOUT,
                    "use_pure": True,
                    "autocommit": False,
                    "charset": 'utf8mb4',
                    "collation": 'utf8mb4_unicode_ci'
                }
                self._pool = MySQLConnectionPool(**dbconfig)
                logger.info("Database connection pool initialized successfully")
            except Error as e:
                logger.error(f"Error initializing connection pool: {e}")
                raise DatabaseError("Failed to initialize database pool")

    def get_connection(self):
        try:
            conn = self._pool.get_connection()
            conn.autocommit = False
            return conn
        except Error as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise DatabaseError("Failed to get database connection")


def with_retry(max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """Decorator for retry logic."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (Error, DatabaseError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed in {func.__name__}, retrying in {delay}s...")
                        time.sleep(delay)
            logger.error(f"All {max_retries} attempts failed in {func.__name__}: {last_error}")
            raise last_error
        return wrapper
    return decorator


@with_retry()
def insert_invoice_data(
    billing_organization_name: str,
    billing_address: str = None,
    billing_contact_information: str = None,
    billing_phone_number: str = None,
    billing_gst_number: str = None,
    billing_hsn_number: str = None,
    shipping_organization_name: str = None,
    shipping_address: str = None,
    shipping_contact_information: str = None,
    shipping_phone_number: str = None,
    shipping_gst_number: str = None,
    shipping_hsn_number: str = None,
    invoice_number: str = None,
    invoice_date: str = None,
    due_date: str = None,
    po_number: str = None,
    payment_terms: str = None,
    delivery_date: str = None,
    currency: str = "INR",
    subtotal: str = "0",
    discount: str = "0",
    tax_amount: str = "0",
    total_amount: str = "0",
    terms_conditions: str = None,
    notes: str = None,
    line_items: List[Dict] = None,
    submission_id: str = None,
    verification_status: str = "VERIFIED",
    file_path: str = None
) -> bool:
    """Insert invoice data with validation and transaction management."""
    def clean_amount_input(amount_str):
        if not amount_str or str(amount_str).upper() == "NA":
            return "0"
        return str(amount_str).replace(',', '').strip()
    subtotal = clean_amount_input(subtotal)
    total_amount = clean_amount_input(total_amount)
    tax_amount = clean_amount_input(tax_amount)
    discount = clean_amount_input(discount)
    file_name = os.path.basename(file_path) if file_path else file_path
    invoice_date = normalize_date(invoice_date) or None
    due_date = normalize_date(due_date) or None
    delivery_date = normalize_date(delivery_date) or None
    print("i am inside the insert_po_dataaaaaaaaaaaaaaaaaaaaaaaaaaa")
    print("INVOICE DATA:", billing_organization_name, invoice_number, invoice_date, due_date, total_amount, subtotal, tax_amount, discount, currency)
    if not validate_invoice_number(invoice_number):
        raise ValidationError("Invalid invoice number format")
    if invoice_date and not validate_date(invoice_date):
        raise ValidationError("Invalid invoice date format (YYYY-MM-DD)")
    if due_date and not validate_date(due_date):
        raise ValidationError("Invalid due date format (YYYY-MM-DD)")
    if delivery_date and not validate_date(delivery_date):
        raise ValidationError("Invalid delivery date format (YYYY-MM-DD)")
    if not validate_amount(total_amount):
        raise ValidationError("Invalid total amount format")
    if not validate_amount(subtotal):
        raise ValidationError("Invalid subtotal format")
    if not validate_amount(tax_amount):
        raise ValidationError("Invalid tax amount format")
    if not validate_amount(discount):
        raise ValidationError("Invalid discount format")
    if not validate_currency(currency):
        raise ValidationError("Invalid currency code")

    conn = None
    cursor = None
  
    def clean_decimal_str(value: str) -> str:
        if not value:
            return "0"
        value = str(value).replace(',', '')
        return re.sub(r'[^\d.]', '', value)

    try:
        conn = DatabasePool.get_instance().get_connection()
        cursor = conn.cursor()
        conn.start_transaction()

        decimal_total = Decimal(clean_decimal_str(total_amount))
        decimal_subtotal = Decimal(clean_decimal_str(subtotal))
        decimal_tax = Decimal(clean_decimal_str(tax_amount))
        decimal_discount = Decimal(clean_decimal_str(discount))
        current_time = datetime.now()

        logger.debug(f"Raw line items: {line_items}")
        validated_line_items = validate_line_items(line_items) if line_items else []
        logger.debug(f"Validated line items: {validated_line_items}")

        try:
            line_items_json = json.dumps(validated_line_items, default=str)
            logger.debug(f"Line items JSON to store: {line_items_json}")
        except Exception as e:
            logger.error(f"JSON serialization error for line items: {e}")
            cleaned_items = [{k: str(v) for k, v in item.items()} for item in validated_line_items]
            line_items_json = json.dumps(cleaned_items)
            logger.warning("Used fallback serialization for line items")

        invoice_query = """
            INSERT INTO Invoice_Data (
                billing_organization_name, billing_address, billing_contact_information,
                billing_phone_number, billing_gst_number, billing_hsn_number,
                shipping_organization_name, shipping_address, shipping_contact_information,
                shipping_phone_number, shipping_gst_number, shipping_hsn_number,
                invoice_number, invoice_date, due_date, po_number,
                payment_terms, delivery_date, currency, subtotal,
                discount, tax_amount, total_amount, terms_conditions,
                notes, line_items, verification_status, file_name, extracted_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s)
        """
        invoice_params = (
            billing_organization_name, billing_address, billing_contact_information,
            billing_phone_number, billing_gst_number, billing_hsn_number,
            shipping_organization_name, shipping_address, shipping_contact_information,
            shipping_phone_number, shipping_gst_number, shipping_hsn_number,
            invoice_number, invoice_date, due_date, po_number,
            payment_terms, delivery_date, currency.upper(),
            decimal_subtotal, decimal_discount, decimal_tax, decimal_total,
            terms_conditions, notes, line_items_json,
            verification_status, file_name, current_time
        )

        cursor.execute(invoice_query, invoice_params)

        if submission_id:
            track_query = """
                INSERT INTO submission_tracking (
                    submission_id, billing_organization_name, invoice_number,
                    file_name, verification_status, submission_time, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            track_params = (
                submission_id, billing_organization_name, invoice_number,
                file_name, verification_status, current_time, 'SUCCESS'
            )
            cursor.execute(track_query, track_params)
        else:
            print(f"No submission_id provided for invoice {invoice_number} of {billing_organization_name}")

        conn.commit()
        logger.info(f"Inserted invoice data for {billing_organization_name}, Invoice: {invoice_number}, ID: {submission_id}")
        logger.info(f"Stored {len(validated_line_items)} line items as JSON")
        return True

    except Error as e:
        if conn:
            try:
                conn.rollback()
            except Error as rollback_error:
                logger.error(f"Rollback error: {rollback_error}")
        logger.error(f"Database insertion error: {e}")
        raise DatabaseError(f"Failed to insert invoice data: {str(e)}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@with_retry()
def is_duplicate_submission(submission_id: str) -> bool:
    """Checks whether the given submission_id already exists."""
    print("I am in is_duplicate_submissionnnnnnnnnnnnnnnnnnnnnnnnnn")
    if not submission_id or not isinstance(submission_id, str):
        return False
    conn = None
    cursor = None
    try:
        conn = DatabasePool.get_instance().get_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT 1 FROM submission_tracking WHERE submission_id = %s LIMIT 1
        """
        cursor.execute(query, (submission_id,))
        result = cursor.fetchone()
        print(result,"resultssssssssssssssssssssssssssssssssssssssssssss")
        if result:
            print(f"Duplicate submission detected: {submission_id}")
            return True
        return False
    except Error as e:
        print(f"Duplicate check error: {e}")
        raise DatabaseError(f"Duplicate check failed: {str(e)}")
    finally:
        if conn:
            conn.close()

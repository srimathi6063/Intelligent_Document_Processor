import smtplib
import os
import tempfile
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

def send_invoice_email(filename, extracted_data, original_file_path=None, recipient_email=None, edited_data=None):
    """
    Send email with invoice processing results and both input and output files as attachments.
    Uses edited_data if provided, otherwise use extracted_data.
    """
    try:
        # Use edited_data if provided, otherwise use extracted_data
        data_to_use = edited_data if edited_data is not None else extracted_data
        
        # Create Excel file with the data (edited or original)
        excel_data = []
        
        # Add billing information
        excel_data.append(['Billing Information', ''])
        excel_data.append(['Organization Name', data_to_use.get('billing_organization_name', '')])
        excel_data.append(['Address', data_to_use.get('billing_address', '')])
        excel_data.append(['Contact Information', data_to_use.get('billing_contact_information', '')])
        excel_data.append(['Phone Number', data_to_use.get('billing_phone_number', '')])
        excel_data.append(['GST Number', data_to_use.get('billing_gst_number', '')])
        excel_data.append(['HSN Number', data_to_use.get('billing_hsn_number', '')])
        excel_data.append(['', ''])
        
        # Add shipping information
        excel_data.append(['Shipping Information', ''])
        excel_data.append(['Organization Name', data_to_use.get('shipping_organization_name', '')])
        excel_data.append(['Address', data_to_use.get('shipping_address', '')])
        excel_data.append(['Contact Information', data_to_use.get('shipping_contact_information', '')])
        excel_data.append(['Phone Number', data_to_use.get('shipping_phone_number', '')])
        excel_data.append(['GST Number', data_to_use.get('shipping_gst_number', '')])
        excel_data.append(['HSN Number', data_to_use.get('shipping_hsn_number', '')])
        excel_data.append(['', ''])
        
        # Add document information
        excel_data.append(['Document Information', ''])
        excel_data.append(['Invoice Number', data_to_use.get('invoice_number', '')])
        excel_data.append(['Invoice Date', data_to_use.get('invoice_date', '')])
        excel_data.append(['Due Date', data_to_use.get('due_date', '')])
        excel_data.append(['PO Number', data_to_use.get('po_number', '')])
        excel_data.append(['Payment Terms', data_to_use.get('payment_terms', '')])
        excel_data.append(['Delivery Date', data_to_use.get('delivery_date', '')])
        excel_data.append(['Currency', data_to_use.get('currency', '')])
        excel_data.append(['', ''])
        
        # Add financial information
        excel_data.append(['Financial Information', ''])
        excel_data.append(['Subtotal', data_to_use.get('subtotal', '')])
        excel_data.append(['Discount', data_to_use.get('discount', '')])
        excel_data.append(['Tax Amount', data_to_use.get('tax_amount', '')])
        excel_data.append(['Total Amount', data_to_use.get('total_amount', '')])
        excel_data.append(['', ''])
        
        # Add line items
        if data_to_use.get('line_items'):
            excel_data.append(['Line Items', '', '', '', ''])
            excel_data.append(['S.No', 'Description', 'Quantity', 'Unit Price', 'Total'])
            for item in data_to_use['line_items']:
                excel_data.append([
                    item.get('S.NO', ''),
                    item.get('description', ''),
                    item.get('quantity', ''),
                    item.get('unit_price', ''),
                    item.get('total_per_product', '')
                ])
        
        # Create temporary Excel file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            df = pd.DataFrame(excel_data)
            df.to_excel(tmp_file.name, index=False, header=False)
            excel_path = tmp_file.name
        
        # Email content
        data_source = "Edited" if edited_data is not None else "Extracted"
        subject = f"Invoice Processing Complete - {filename}"
        body = f"""Hi,

The document has been successfully processed. Please find the input and output files attached for your reference.

📄 Processed File: {filename}
✅ Status: Successfully processed with AI
📝 Data Source: {data_source} data (user-reviewed and edited)

📊 Processing Information:
• Document Type: Invoice/Purchase Order
• Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Workflow: Invoice Processing
• Data Type: {data_source} data
• Extracted Fields: {len([k for k, v in data_to_use.items() if v and k != 'line_items'])} fields

The AI has extracted all relevant information including billing details, shipping information, line items, and financial data. This data has been reviewed and edited by the user.

📎 Attachments:
• Input File: {filename} (Original uploaded document)
• Output File: {filename.replace('.', '_')}_extracted_data.xlsx ({data_source} data in Excel format)

Thanks,
Uniware systems support team"""

        # Prepare attachments
        attachments = [
            {
                'path': excel_path,
                'name': f"{filename.replace('.', '_')}_extracted_data.xlsx"
            }
        ]
        
        # Add original file if path is provided and file exists
        if original_file_path and os.path.exists(original_file_path):
            logger.info(f"Adding original file attachment: {filename} from {original_file_path}")
            attachments.append({
                'path': original_file_path,
                'name': filename
            })
        else:
            logger.warning(f"Original file not found or path not provided: {original_file_path}")
            logger.info(f"Will send email with only Excel attachment: {filename.replace('.', '_')}_extracted_data.xlsx")

        # Send email with multiple attachments
        email_sent = send_email_with_multiple_attachments(
            subject=subject,
            body=body,
            attachments=attachments,
            recipient_email=recipient_email
        )
        
        # Clean up temporary file
        if os.path.exists(excel_path):
            os.unlink(excel_path)
        
        if email_sent:
            logger.info(f"Email sent successfully for invoice processing: {filename}")
            return True
        else:
            logger.error(f"Email sending failed for invoice processing: {filename}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to send invoice email: {e}")
        # Clean up temporary file if it exists
        if 'excel_path' in locals() and os.path.exists(excel_path):
            os.unlink(excel_path)
        return False

def send_summarization_email(filename, summary, original_file_path=None, recipient_email=None, edited_summary=None):
    """
    Send email with document summarization results and both input and output files as attachments.
    Uses edited_summary if provided, otherwise uses summary.
    """
    try:
        # Use edited_summary if provided, otherwise use summary
        summary_to_use = edited_summary if edited_summary is not None else summary
        
        # Create temporary text file with the summary (edited or original)
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(summary_to_use)
            text_path = tmp_file.name
        
        # Email content
        summary_source = "Edited" if edited_summary is not None else "Generated"
        subject = f"Document Summarization Complete - {filename}"
        body = f"""Hi,

The document has been successfully summarized. Please find the input and output files attached for your reference.

📄 Processed File: {filename}
✅ Status: Successfully summarized with AI
📝 Summary Source: {summary_source} summary (user-reviewed and edited)

📊 Summary Information:
• Document Type: Summary generated
• Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Workflow: Document Summarization
• Summary Type: {summary_source} summary

The AI has created a comprehensive summary of your document with all key information, main points, and important details. This summary has been reviewed and edited by the user.

📎 Attachments:
• Input File: {filename} (Original uploaded document)
• Output File: {filename.replace('.', '_')}_summary.txt ({summary_source} summary)

Thanks,
Uniware systems support team"""

        # Prepare attachments
        attachments = [
            {
                'path': text_path,
                'name': f"{filename.replace('.', '_')}_summary.txt"
            }
        ]
        
        # Add original file if path is provided and file exists
        if original_file_path and os.path.exists(original_file_path):
            logger.info(f"Adding original file attachment: {filename} from {original_file_path}")
            attachments.append({
                'path': original_file_path,
                'name': filename
            })
        else:
            logger.warning(f"Original file not found or path not provided: {original_file_path}")
            logger.info(f"Will send email with only summary attachment: {filename.replace('.', '_')}_summary.txt")

        # Send email with multiple attachments
        send_email_with_multiple_attachments(
            subject=subject,
            body=body,
            attachments=attachments,
            recipient_email=recipient_email
        )
        
        # Clean up temporary file
        os.unlink(text_path)
        
        logger.info(f"Email sent successfully for document summarization: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send summarization email: {e}")
        return False

def send_email_with_multiple_attachments(subject, body, attachments, recipient_email=None):
    """
    Send email with multiple attachments using SMTP.
    """
    try:
        # Use default recipient if none provided
        if not recipient_email:
            recipient_email = settings.EMAIL_CONFIG['recipient_email']
        
        logger.info(f"Attempting to send email to: {recipient_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Number of attachments: {len(attachments)}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_CONFIG['sender_email']
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add all attachments
        for attachment in attachments:
            if os.path.exists(attachment['path']):
                logger.info(f"Adding attachment: {attachment['name']} from {attachment['path']}")
                with open(attachment['path'], 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["name"]}'
                )
                msg.attach(part)
            else:
                logger.warning(f"Attachment file not found: {attachment['path']}")
        
        # Send email
        logger.info(f"Connecting to SMTP server: {settings.EMAIL_CONFIG['smtp_server']}:{settings.EMAIL_CONFIG['smtp_port']}")
        server = smtplib.SMTP(settings.EMAIL_CONFIG['smtp_server'], settings.EMAIL_CONFIG['smtp_port'])
        server.starttls()
        logger.info("SMTP connection established, attempting login...")
        server.login(settings.EMAIL_CONFIG['sender_email'], settings.EMAIL_CONFIG['sender_password'])
        logger.info("SMTP login successful, sending email...")
        text = msg.as_string()
        server.sendmail(settings.EMAIL_CONFIG['sender_email'], recipient_email, text)
        server.quit()
        logger.info("SMTP connection closed")
        
        logger.info(f"Email sent successfully to {recipient_email} with {len(attachments)} attachments")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_email_with_attachment(subject, body, attachment_path, attachment_name, recipient_email=None):
    """
    Send email with single attachment using SMTP (kept for backward compatibility).
    """
    return send_email_with_multiple_attachments(
        subject=subject,
        body=body,
        attachments=[{'path': attachment_path, 'name': attachment_name}],
        recipient_email=recipient_email
    )

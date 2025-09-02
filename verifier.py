import json
import logging
from typing import Dict, Any, List
from utils.llm_helper import call_bedrock_verification

logger = logging.getLogger(__name__)


class VerificationAgent:
    def __init__(self):
        try:
            logger.info("VerificationAgent initialized successfully with AWS Bedrock.")
        except Exception as e:
            logger.error(f"Failed to initialize VerificationAgent: {e}")
            raise

    def _build_prompt(self, extracted_json: Dict[str, Any], context_text: str) -> str:
        """
        Builds a prompt to verify the extracted invoice fields against the document text.
        """
        # Pretty format JSON with indentation for visibility in prompt
        json_str = json.dumps(extracted_json, indent=2, ensure_ascii=False)

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
{json_str}

### Document Text:
{context_text}

Only respond with the JSON above, do NOT include anything else.
"""
        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parses the LLM's JSON response text into a Python dictionary.
        """
        try:
            # Heuristic: LLM may sometimes add backticks or extra text - extract valid JSON part
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_part = response_text[start:end]
            verification = json.loads(json_part)

            # Validate keys presence with fallback defaults
            verification.setdefault("Supported", "NO")
            verification.setdefault("Unsupported Claims", [])
            verification.setdefault("Contradictions", [])
            verification.setdefault("Relevant", "NO")
            verification.setdefault("Additional Details", "")

            return verification
        except Exception as e:
            logger.error(f"Failed to parse verification response JSON: {e}")
            return {
                "Supported": "NO",
                "Unsupported Claims": [],
                "Contradictions": [],
                "Relevant": "NO",
                "Additional Details": f"Parsing error: {e}"
            }

    def format_report(self, verification: Dict[str, Any]) -> str:
        """
        Formats the verification dictionary into a user-readable report string.
        """
        lines = []
        lines.append(f"Supported: {verification.get('Supported', 'NO')}")
        
        uc = verification.get('Unsupported Claims', [])
        lines.append(f"Unsupported Claims: {', '.join(uc) if uc else 'None'}")
        
        ct = verification.get('Contradictions', [])
        lines.append(f"Contradictions: {', '.join(ct) if ct else 'None'}")
        
        lines.append(f"Relevant: {verification.get('Relevant', 'NO')}")
        
        add_details = verification.get('Additional Details', '').strip()
        lines.append(f"Additional Details: {add_details if add_details else 'None'}")

        return "\n".join(lines)

    def check(self, extracted_json: Dict[str, Any], context_text: str) -> Dict[str, str]:
        """
        Verifies the extracted JSON invoice data against the document text using AWS Bedrock.

        Args:
            extracted_json: The JSON data extracted from the document.
            context_text: The full extracted text from the invoice document.

        Returns:
            A dictionary containing:
            - "verification_report": The formatted verification summary.
            - "raw_llm_response": The raw verification JSON string from the model (for debugging).
        """
        prompt = self._build_prompt(extracted_json, context_text)

        try:
            logger.debug("Sending verification prompt to AWS Bedrock.")
            
            # Use the dedicated verification function
            verification_dict = call_bedrock_verification(extracted_json, context_text)
            
            verification_report = self.format_report(verification_dict)

            return {
                "verification_report": verification_report,
                "raw_llm_response": str(verification_dict)
            }

        except Exception as e:
            logger.error(f"Error during verification AWS Bedrock call: {e}")
            return {
                "verification_report": f"Verification failed: {e}",
                "raw_llm_response": ""
            }

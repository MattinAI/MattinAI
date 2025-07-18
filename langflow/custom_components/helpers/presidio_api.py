from typing import Dict, List, Optional, Any
from langflow.custom import Component
from langflow.inputs import DropdownInput, FloatInput, MessageTextInput
from langflow.template import Output
from langflow.schema.message import Message
from langflow.logging import logger
import requests
import json

class PresidioPIIComponentAPI(Component):
    display_name = "Presidio Server API"
    description = "Detect and anonymize PII in text using Microsoft Presidio API"
    icon = "shield-check"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input Text",
            info="Text to process for PII detection",
        ),
        MessageTextInput(
            name="anonymization_api_url",
            display_name="Anonymization API URL",
            info="Anonymization API endpoint URL",
            value="http://localhost:8000/anonymization_service/anonymize",
        ),
        DropdownInput(
            name="model_family",
            display_name="Model Family",
            info="NLP model type to use for entity detection",
            options=["spaCy", "flair"],
            value="spaCy",
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            info="Model name within the selected family",
            options=["en_core_web_lg", "ner-english"],
            value="en_core_web_lg",
        ),
        FloatInput(
            name="threshold",
            display_name="Confidence Threshold",
            info="Minimum confidence score for entity detection (0.0-1.0)",
            value=0.4,
        )
    ]

    outputs = [
        Output(display_name="Response", name="response", method="process_text"),
    ]

    def process_text(self) -> Message:
        """Process text for PII detection and anonymization via API."""
        try:
            # Get the text to process
            text = self.input_text
            
            # If we received a Message object, extract its text
            if isinstance(text, Message):
                text = text.text
                
            if not text:
                return Message(text="No input text provided.")

            try:
                # Prepare API request
                payload = {
                    "text": text,
                    "model_family": self.model_family,
                    "model_name": self.model_name,
                    "threshold": self.threshold,
                }
                
                # Call the API
                response = requests.post(
                    self.anonymization_api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )

                # Handle response
                if response.status_code == 200:
                    result = response.json()
                    return Message(text=json.dumps(result))
                else:
                    error_message = f"API error: {response.status_code} - {response.text}"
                    logger.error(error_message)
                    return Message(text=error_message)

            except Exception as e:
                logger.error(f"Error calling Presidio API: {e}")
                return Message(text=f"Error calling Presidio API: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return Message(text=f"Error processing text: {str(e)}")
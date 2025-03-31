# from langflow.field_typing import Data
from langflow.custom import Component
from langflow.io import (
    FileInput, 
    TextOutput,
    SelectInput,
    FloatInput,
    TextInput,
    BooleanInput,
    ListInput
)
from langflow.schema import Data
from anonymizer.processor import PresidioProcessor

class CustomComponent(Component):
    display_name = "Anonymizer"
    description = "Anonymize a text using Composio from Microsoft by detecting and replacing PII"
    documentation: str = "https://microsoft.github.io/presidio/"
    icon = "document"
    name = "CVAnonymizer"

    inputs = [
        TextInput(
            name="cv_file",
            display_name="CV text",
            description="Upload the candidate's resume or CV (TXT)",
        ),
        SelectInput(
            name="model_family",
            display_name="NER Model Family",
            description="NER model package to use for entity detection",
            options=["spaCy", "Flair", "HuggingFace", "stanza", "Azure AI Language"],
            value="spaCy",
        ),
        TextInput(
            name="model_name",
            display_name="Model Name",
            description="Model name within the package",
            value="en_core_web_lg",
        ),
        FloatInput(
            name="threshold",
            display_name="Detection Threshold",
            description="Confidence threshold for entity detection (0.0 to 1.0)",
            value=0.4,
        ),
        SelectInput(
            name="operator",
            display_name="Anonymization Method",
            description="Method to use for anonymizing detected entities",
            options=["replace", "redact", "mask", "hash", "encrypt", "highlight"],
            value="replace",
        ),
        TextInput(
            name="mask_char",
            display_name="Mask Character",
            description="Character to use for masking (if mask method selected)",
            value="*",
        ),
        FloatInput(
            name="number_of_chars",
            display_name="Number of Chars",
            description="Number of characters to mask (if mask method selected)",
            value=15,
        ),
        TextInput(
            name="encrypt_key",
            display_name="Encryption Key",
            description="Key for encryption (if encrypt method selected)",
            value="WmZq4t7w!z%C&F)J",
            password=True,
        ),
        ListInput(
            name="allow_list",
            display_name="Allow List",
            description="Words to be excluded from detection (e.g., company names)",
            value=[],
        ),
        ListInput(
            name="deny_list",
            display_name="Deny List",
            description="Words to be included in detection",
            value=[],
        ),
        BooleanInput(
            name="return_decision_process",
            display_name="Return Decision Process",
            description="Whether to return decision process details",
            value=False,
        ),
    ]

    outputs = [
        TextOutput(display_name="Anonymized CV", name="anonymized_cv", method="anonymize_cv"),
        TextOutput(display_name="Detected Entities", name="detected_entities", method="get_entities")
    ]

    def anonymize_cv(self) -> str:
        """Process the CV and return anonymized content."""
        if not self.cv_file:
            return "No file uploaded."
        
        # Extract text from the uploaded file
        cv_text = self.read_file_content(self.cv_file)
        
        # Initialize Presidio processor
        processor = PresidioProcessor()
        
        # Setup the processor with provided configuration
        processor.setup(
            model_family=self.model_family,
            model_name=self.model_name,
            threshold=float(self.threshold),
            return_decision_process=self.return_decision_process,
            allow_list=self.allow_list,
            deny_list=self.deny_list
        )
        
        # Process the text
        try:
            anonymized_text, entities = processor.process_text(
                text=cv_text,
                operator=self.operator,
                mask_char=self.mask_char,
                number_of_chars=int(self.number_of_chars),
                encrypt_key=self.encrypt_key
            )
            
            # Store entities for the second output
            self._entities = entities
            
            return anonymized_text
        except Exception as e:
            logger.error(f"Error during anonymization: {e}")
            return f"Error during anonymization: {str(e)}"

    def get_entities(self) -> str:
        """Return detected entities as formatted text."""
        if not hasattr(self, '_entities'):
            return "No entities detected or CV not processed."
            
        if not self._entities:
            return "No PII entities were detected in the document."
            
        # Format entities into readable text
        entities_text = "Detected PII Entities:\n\n"
        for entity in self._entities:
            entities_text += f"- {entity['entity_type']}: '{entity['text']}' (confidence: {entity['score']:.2f})\n"
            
        return entities_text

    def build_output(self) -> Data:
        data = Data(value=self.input_value)
        self.status = data
        return data

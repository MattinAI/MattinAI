import logging
from typing import List, Dict, Any

# Import the helper modules directly
from presidio_helpers import presidio_helpers

# Streamlit logger
logging.getLogger("streamlit").setLevel(logging.ERROR)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("presidio-main")

class PresidioProcessor:
    """A wrapper to use Presidio for PII detection and anonymization without Streamlit."""
    
    def __init__(self):
        """Initialize the processor."""
        self.analyzer = None
        self.anonymizer = presidio_helpers.anonymizer_engine()
        
    def setup(
        self,
        model_family: str = "spaCy",
        model_name: str = "en_core_web_lg",
        ta_key: str = "",
        ta_endpoint: str = "",
        threshold: float = 0.4,
        return_decision_process: bool = False,
        allow_list: List[str] = None,
        deny_list: List[str] = None,
        entities_to_analyze: List[str] = None,
    ):
        """Configure the PII processor.
        
        Args:
            model_family: NER model package ("spaCy", "Flair", "HuggingFace", "stanza", or "Azure AI Language")
            model_name: Model name within the package
            ta_key: Azure Text Analytics key (only for Azure AI Language)
            ta_endpoint: Azure Text Analytics endpoint (only for Azure AI Language)
            threshold: Confidence threshold for entity detection
            return_decision_process: Whether to return decision process details
            allow_list: List of words to be excluded from detection
            deny_list: List of words to be included in detection
            entities_to_analyze: List of entity types to detect
        """
        logger.info(f"Setting up processor with {model_family}/{model_name}")
        
        # Initialize the analyzer
        self.analyzer = presidio_helpers.analyzer_engine(
            model_family, model_name, ta_key, ta_endpoint
        )
        
        # Store configuration
        self.model_family = model_family
        self.model_name = model_name
        self.ta_key = ta_key
        self.ta_endpoint = ta_endpoint
        self.threshold = threshold
        self.return_decision_process = return_decision_process
        self.allow_list = allow_list or []
        self.deny_list = deny_list or []
        
        # Get supported entities
        self.supported_entities = presidio_helpers.get_supported_entities(
            model_family, model_name, ta_key, ta_endpoint
        )
        logger.info(f"Supported entities: {self.supported_entities}")
        
        # Set entities to analyze
        if entities_to_analyze:
            self.entities_to_analyze = [e for e in entities_to_analyze if e in self.supported_entities]
            if len(entities_to_analyze) != len(self.entities_to_analyze):
                logger.warning("Some requested entities are not supported by the model")
        else:
            self.entities_to_analyze = self.supported_entities
    
    def analyze(self, text: str):
        """Analyze text for PII entities.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of detected entities
        """
        if not self.analyzer:
            raise ValueError("Analyzer not initialized. Call setup() first.")
        
        # Prepare analyze parameters
        analyze_params = {
            "text": text,
            "entities": self.entities_to_analyze,
            "language": "en",
            "score_threshold": self.threshold,
            "return_decision_process": self.return_decision_process,
            "allow_list": self.allow_list,
            "deny_list": self.deny_list,
        }
        
        # Analyze the text using the helper function
        results = presidio_helpers.analyze(
            self.model_family, 
            self.model_name, 
            self.ta_key, 
            self.ta_endpoint, 
            **analyze_params
        )
        
        return results
    
    def anonymize(
        self, 
        text: str, 
        analyze_results, 
        operator: str = "replace",
        mask_char: str = "*",
        number_of_chars: int = 15,
        encrypt_key: str = "WmZq4t7w!z%C&F)J"
    ):
        """Anonymize PII entities in text.
        
        Args:
            text: The text to anonymize
            analyze_results: Results from analyze()
            operator: The anonymization operator to use
            mask_char: Character to use for masking
            number_of_chars: Number of characters to mask
            encrypt_key: Key for encryption
            
        Returns:
            Anonymized text
        """
        # Use the helper function for anonymization
        anonymized_result = presidio_helpers.anonymize(
            text=text,
            operator=operator,
            analyze_results=analyze_results,
            mask_char=mask_char,
            number_of_chars=number_of_chars,
            encrypt_key=encrypt_key,
        )
        
        return anonymized_result
    
    def annotate(self, text: str, analyze_results):
        """Generate annotated version of the text.
        
        Args:
            text: The text to annotate
            analyze_results: Results from analyze()
            
        Returns:
            List of annotated tokens
        """
        return presidio_helpers.annotate(text, analyze_results)
        
    def process_text(
        self, 
        text: str, 
        operator: str = "replace",
        mask_char: str = "*",
        number_of_chars: int = 15,
        encrypt_key: str = "WmZq4t7w!z%C&F)J",
    ):
        """Process text for PII detection and anonymization.
        
        Args:
            text: The text to process
            operator: The anonymization operator to use
            mask_char: Character to use for masking
            number_of_chars: Number of characters to mask
            encrypt_key: Key for encryption
            
        Returns:
            Tuple of (processed text, list of detected entities)
        """
        # Analyze the text
        analyze_results = self.analyze(text)
        
        # If no entities found, return original text
        if not analyze_results:
            return text, []
        
        # Prepare result entities for return
        entities = []
        for result in analyze_results:
            entity = result.to_dict()
            entity["text"] = text[result.start:result.end]
            entities.append(entity)
        
        # If we just want to highlight, return the original text and entities
        if operator == "highlight":
            return text, entities
        
        # For all other operators, anonymize the text
        anonymized_result = self.anonymize(
            text=text,
            analyze_results=analyze_results,
            operator=operator,
            mask_char=mask_char,
            number_of_chars=number_of_chars,
            encrypt_key=encrypt_key
        )
        
        return anonymized_result.text, entities
    
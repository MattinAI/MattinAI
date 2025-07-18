from typing import Dict, List, Optional, Any, Union, Tuple, Set
from langflow.custom import Component
from langflow.inputs import DropdownInput, MultilineInput, FloatInput, BoolInput, MessageTextInput
from langflow.template import Output
from langflow.schema.message import Message
from langflow.logging import logger
# from flair.data import Sentence
# from flair.models import SequenceTagger
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, RecognizerResult, EntityRecognizer, AnalysisExplanation, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpArtifacts
import re

class PresidioNlpEngineFactory:
    "Factory for creating NLP engines for Presisio"

    @staticmethod
    def create_nlp_engine_with_spacy(model_path: str):
        """Create an NLP engine with a spaCy model."""
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": model_path}],
            "ner_model_configuration": {
                "model_to_presidio_entity_mapping": {
                    "PER": "PERSON",
                    "PERSON": "PERSON",
                    "NORP": "NRP",
                    "FAC": "FACILITY",
                    "LOC": "LOCATION",
                    "GPE": "LOCATION",
                    "LOCATION": "LOCATION",
                    "ORG": "ORGANIZATION",
                    "ORGANIZATION": "ORGANIZATION",
                    "DATE": "DATE_TIME",
                    "TIME": "DATE_TIME",
                },
                "low_confidence_score_multiplier": 0.4,
                "low_score_entity_names": ["ORG", "ORGANIZATION"],
            },
        }

        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        return nlp_engine, registry

    @staticmethod
    def get_nlp_engine(model_family: str, model_path: str):
        """Get the appropriate NLP engine based on the model family."""
        if "spacy" in model_family.lower():
            return PresidioNlpEngineFactory.create_nlp_engine_with_spacy(model_path)
        else:
            raise ValueError(f"Model family {model_family} not supported. Use 'spaCy'")

class PresidioProcessor:
    """A wrapper to use Presidio for PII detection and anonymization."""
    
    def __init__(
        self,
        model_family: str = "spaCy",
        model_name: str = "en_core_web_lg",
        threshold: float = 0.4,
        allow_list: List[str] = None,
        deny_list: List[str] = None,
    ):        
        # Get NLP engine and registry
        nlp_engine, registry = PresidioNlpEngineFactory.get_nlp_engine(model_family, model_name)
        
        # Create analyzer
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            registry=registry
        )
        
        # Create anonymizer
        self.anonymizer = AnonymizerEngine()
        
        # Store configuration 
        self.threshold = threshold
        self.allow_list = allow_list or []
        self.deny_list = deny_list or []

        # Add deny list recognizer if provided
        if self.deny_list:
            deny_list_recognizer = PatternRecognizer(
                supported_entity="GENERIC_PII", 
                deny_list=self.deny_list
            )
            self.analyzer.registry.add_recognizer(deny_list_recognizer)
        
        # Get supported entities
        self.supported_entities = self.analyzer.get_supported_entities()
    
    def analyze(self, text: str):
        """Analyze text for PII entities."""
        # Prepare analyze parameters
        analyze_params = {
            "text": text,
            "entities": "", # Detect all supported entities
            "language": "en",
            "score_threshold": self.threshold,
            "allow_list": self.allow_list
        }
        
        # Analyze the text
        results = self.analyzer.analyze(**analyze_params)
        return results
    
    def anonymize(
        self, 
        text: str, 
        analyze_results, 
        operator: str = "replace",
        mask_char: str = "*",
        number_of_chars: int = None,
        encrypt_key: str = "WmZq4t7w!z%C&F)J"
    ):
        """Anonymize PII entities in text."""
        from presidio_anonymizer.entities import OperatorConfig
        
        # Configure operator
        if operator == "mask":
            operator_config = {
                "type": "mask",
                "masking_char": mask_char,
                "chars_to_mask": number_of_chars,
                "from_end": False,
            }
        elif operator == "encrypt":
            operator_config = {"key": encrypt_key}
        elif operator == "highlight":
            operator_config = {"lambda": lambda x: x}
            operator = "custom"  # highlight is implemented as custom
        else:
            operator_config = None
        
        # Anonymize the text
        result = self.anonymizer.anonymize(
            text,
            analyze_results,
            operators={"DEFAULT": OperatorConfig(operator, operator_config)},
        )
        
        return result
    
    def process_text(
        self, 
        text: str, 
        operator: str = "replace",
        mask_char: str = "*",
        number_of_chars: int = None,
        encrypt_key: str = "WmZq4t7w!z%C&F)J",
    ):
        """Process text for PII detection and anonymization."""
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
    
class PresidioPIIComponent(Component):
    display_name = "Presidio PII Processor"
    description = "Detect and anonymize PII in text using Microsoft Presidio"
    icon = "shield-check"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input Text",
            info="Text to process for PII detection",
        ),
        DropdownInput(
            name="model_family",
            display_name="Model Family",
            info="NLP model type to use for entity detection",
            options=["spaCy"],
            value="spaCy",
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            info="Model name within the selected family",
            options=["en_core_web_lg"],
            value="en_core_web_lg",
        ),
        FloatInput(
            name="threshold",
            display_name="Confidence Threshold",
            info="Minimum confidence score for entity detection (0.0-1.0)",
            value=0.4,
        ),
        DropdownInput(
            name="anonymization_method",
            display_name="Anonymization Method",
            info="How to handle detected PII",
            options=["replace", "mask", "hash"],
            value="replace",
        ),
        MultilineInput(
            name="allow_list",
            display_name="Allow List",
            info="Comma-separated list of terms to ignore during detection",
            value="",
        ),
        MultilineInput(
            name="deny_list",
            display_name="Deny List",
            info="Comma-separated list of terms to specifically detect",
            value="",
        ),
        BoolInput(
            name="include_stats",
            display_name="Include Statistics",
            value=True,
            info="Include detection statistics in output"
        ),
        BoolInput(
            name="return_entities",
            display_name="Return Detected Entities",
            info="Include detected entities in the response",
            value=False,
        )
    ]

    outputs = [
        Output(display_name="Response", name="response", method="process_text"),
    ]

    def process_text(self) -> Message:
        """Process text for PII detection and anonymization."""
        try:
            # Get the text to process
            text = self.input_text
            
            # If we received a Message object, extract its text
            if isinstance(text, Message):
                text = text.text
                
            if not text:
                return Message(text="No input text provided.")
            
            # Parse allow and deny lists
            allow_list = [item.strip() for item in self.allow_list.split(",")] if self.allow_list else []
            deny_list = [item.strip() for item in self.deny_list.split(",")] if self.deny_list else []

            try:
                # Create the Presidio processor
                processor = PresidioProcessor(
                    model_family=self.model_family,
                    model_name=self.model_name,
                    threshold=self.threshold,
                    allow_list=allow_list,
                    deny_list=deny_list
                )

                # Process the text
                processed_text, entities = processor.process_text(
                    text=text,
                    operator=self.anonymization_method
                )

                # Add statistics if enabled
                if self.include_stats:
                    entity_counts = {}
                    for entity in entities:
                        entity_type = entity["entity_type"]
                        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
                    
                    stats = "\n\n--- PII Detection Statistics ---\n"
                    if entity_counts:
                        stats += f"Total entities found: {sum(entity_counts.values())}\n"
                        for entity_type, count in entity_counts.items():
                            stats += f"{entity_type}: {count}\n"
                    else:
                        stats += "No entities found."
                    
                    processed_text += stats
                
                # Add entity details if requested
                if self.return_entities and entities:
                    entity_info = "\n\n--- Detected Entities ---\n"
                    for idx, entity in enumerate(entities, 1):
                        entity_info += f"{idx}. {entity['entity_type']} ({entity['score']:.2f}): '{entity['text']}' [position: {entity['start']}-{entity['end']}]\n"
                    processed_text += entity_info

                return Message(text=processed_text)

            except Exception as e:
                logger.error(f"Error using Presidio: {e}")
                return Message(text=f"Error using Presidio: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return Message(text=f"Error processing text: {str(e)}")
        
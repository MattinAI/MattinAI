# from typing import Dict, List, Optional, Any, Union
# from langflow.custom import Component
# from langchain.schema import Document
# from langflow.field_typing import Tool
# from langflow.io import BoolInput, DropdownInput, MultilineInput, Output, FloatInput
# from langflow.schema.message import Message
# from langflow.schema.dotdict import dotdict
# from langflow.logging import logger
# import logging

# from presidio_analyzer import (
#     AnalyzerEngine, 
#     RecognizerRegistry,
#     PatternRecognizer,
#     Pattern
# )
# from presidio_analyzer.nlp_engine import NlpEngine, NlpEngineProvider
# from presidio_anonymizer import AnonymizerEngine
# from presidio_anonymizer.entities import OperatorConfig


# class PresidioNlpEngineFactory:
#     """Factory for creating NLP engines for Presidio."""
    
#     @staticmethod
#     def create_nlp_engine_with_spacy(model_path: str):
#         """Create an NLP engine with a spaCy model."""
#         import spacy

#         try:
#             spacy.load(model_path)
#             logger.info(f"SpaCy model {model_path} loaded successfully")
#         except OSError:
#             try:
#                 logger.info(f"SpaCy model {model_path} not found, attempting to download it...")
#                 # Use subprocess instead of direct spacy.cli.download to avoid system exit
#                 import subprocess
#                 import sys
                
#                 result = subprocess.run(
#                     [sys.executable, "-m", "spacy", "download", model_path],
#                     capture_output=True,
#                     text=True
#                 )
                
#                 if result.returncode != 0:
#                     logger.error(f"Failed to download SpaCy model: {result.stderr}")
#                     raise ValueError(f"Cannot download or find SpaCy model {model_path}. Error: {result.stderr}")
                
#                 logger.info(f"SpaCy model {model_path} downloaded successfully")
#             except Exception as e:
#                 logger.error(f"Error downloading SpaCy model: {str(e)}")
#                 raise ValueError(f"Failed to download SpaCy model {model_path}. Please install it manually with 'python -m spacy download {model_path}'")

#         nlp_configuration = {
#             "nlp_engine_name": "spacy",
#             "models": [{"lang_code": "en", "model_name": model_path}],
#             "ner_model_configuration": {
#                 "model_to_presidio_entity_mapping": {
#                     "PER": "PERSON",
#                     "PERSON": "PERSON",
#                     "NORP": "NRP",
#                     "FAC": "FACILITY",
#                     "LOC": "LOCATION",
#                     "GPE": "LOCATION",
#                     "LOCATION": "LOCATION",
#                     "ORG": "ORGANIZATION",
#                     "ORGANIZATION": "ORGANIZATION",
#                     "DATE": "DATE_TIME",
#                     "TIME": "DATE_TIME",
#                 },
#                 "low_confidence_score_multiplier": 0.4,
#                 "low_score_entity_names": ["ORG", "ORGANIZATION"],
#             },
#         }

#         try:
#             nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
#             registry = RecognizerRegistry()
#             registry.load_predefined_recognizers(nlp_engine=nlp_engine)
#             return nlp_engine, registry
#         except Exception as e:
#             logger.error(f"Error creating NLP engine: {str(e)}")
#             raise ValueError(f"Failed to create NLP engine with model {model_path}: {str(e)}")
    
#     @staticmethod
#     def create_nlp_engine_with_transformers(model_path: str):
#         """Create an NLP engine with a HuggingFace Transformers model."""
#         nlp_configuration = {
#             "nlp_engine_name": "transformers",
#             "models": [
#                 {
#                     "lang_code": "en",
#                     "model_name": {"spacy": "en_core_web_sm", "transformers": model_path},
#                 }
#             ],
#             "ner_model_configuration": {
#                 "model_to_presidio_entity_mapping": {
#                     "PER": "PERSON",
#                     "PERSON": "PERSON",
#                     "LOC": "LOCATION",
#                     "LOCATION": "LOCATION",
#                     "GPE": "LOCATION",
#                     "ORG": "ORGANIZATION",
#                     "ORGANIZATION": "ORGANIZATION",
#                     "NORP": "NRP",
#                     "AGE": "AGE",
#                     "ID": "ID",
#                     "EMAIL": "EMAIL",
#                     "PATIENT": "PERSON",
#                     "STAFF": "PERSON",
#                     "HOSP": "ORGANIZATION",
#                     "PATORG": "ORGANIZATION",
#                     "DATE": "DATE_TIME",
#                     "TIME": "DATE_TIME",
#                     "PHONE": "PHONE_NUMBER",
#                     "HCW": "PERSON",
#                     "HOSPITAL": "ORGANIZATION",
#                     "FACILITY": "LOCATION",
#                 },
#                 "low_confidence_score_multiplier": 0.4,
#                 "low_score_entity_names": ["ID"],
#                 "labels_to_ignore": [
#                     "CARDINAL",
#                     "EVENT",
#                     "LANGUAGE",
#                     "LAW",
#                     "MONEY",
#                     "ORDINAL",
#                     "PERCENT",
#                     "PRODUCT",
#                     "QUANTITY",
#                     "WORK_OF_ART",
#                 ],
#             },
#         }

#         nlp_engine = NlpEngineProvider(nlp_configuration=nlp_configuration).create_engine()
#         registry = RecognizerRegistry()
#         registry.load_predefined_recognizers(nlp_engine=nlp_engine)

#         return nlp_engine, registry

#     @staticmethod
#     def get_nlp_engine(model_family: str, model_path: str):
#         """Get the appropriate NLP engine based on the model family."""
#         if "spacy" in model_family.lower():
#             return PresidioNlpEngineFactory.create_nlp_engine_with_spacy(model_path)
#         elif "huggingface" in model_family.lower():
#             return PresidioNlpEngineFactory.create_nlp_engine_with_transformers(model_path)
#         else:
#             raise ValueError(f"Model family {model_family} not supported. Use 'spaCy' or 'HuggingFace'")


# class PresidioPIIProcessor(Component):
#     """
#     A component that uses Presidio to detect and anonymize PII in text documents.
#     """
#     display_name = "Presidio PII Processor"
#     description = "Detect and anonymize PII in text using Presidio."
#     icon = "⚙️"
    
#     inputs = [
#         MultilineInput(
#             name="input_text",
#             display_name="Input Text",
#             info="Text to process for PII",
#             value="",
#         ),
#         DropdownInput(
#             name="model_family",
#             display_name="Model Family",
#             info="NLP model type to use for entity detection",
#             options=["spaCy", "HuggingFace"],
#             value="spaCy",
#         ),
#         DropdownInput(
#             name="model_name",
#             display_name="Model Name",
#             info="Model name within the selected family",
#             options=["en_core_web_sm", "en_core_web_lg", "en_core_web_trf"],
#             value="en_core_web_lg",
#         ),
#         FloatInput(
#             name="threshold",
#             display_name="Confidence Threshold",
#             info="Minimum confidence score for entity detection (0.0-1.0)",
#             value=0.4,
#         ),
#         DropdownInput(
#             name="operator",
#             display_name="Anonymization Method",
#             info="How to handle detected PII",
#             options=["replace", "mask", "redact", "encrypt", "hash", "highlight"],
#             value="replace",
#         ),
#         MultilineInput(
#             name="allow_list",
#             display_name="Allow List",
#             info="Comma-separated list of terms to ignore during detection",
#             value="",
#             advanced=True,
#         ),
#         MultilineInput(
#             name="deny_list",
#             display_name="Deny List",
#             info="Comma-separated list of terms to specifically detect",
#             value="",
#             advanced=True,
#         ),
#         BoolInput(
#             name="return_entities",
#             display_name="Return Detected Entities",
#             info="Include detected entities in the response",
#             value=False,
#             advanced=True,
#         ),
#     ]
    
#     outputs = [
#         Output(name="processed_output", display_name="Processed Output", method="process_pii"),
#         Output(name="message_response", display_name="Message Response", method="message_response"),
#     ]

#     async def process_pii(self) -> Union[str, List[Document], Dict[str, Any]]:
#         """Process input for PII detection and anonymization."""
#         try:            
#             # Parse allow and deny lists
#             allow_list = [item.strip() for item in self.allow_list.split(",")] if self.allow_list else []
#             deny_list = [item.strip() for item in self.deny_list.split(",")] if self.deny_list else []
            
#             try:
#                 # Create processor
#                 processor = PresidioProcessor(
#                     model_family=self.model_family,
#                     model_name=self.model_name,
#                     threshold=self.threshold,
#                     allow_list=allow_list if allow_list else None,
#                     deny_list=deny_list if deny_list else None
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to initialize Presidio processor: {str(e)}")
#                 raise ValueError(f"Failed to initialize Presidio processor with {self.model_family} model {self.model_name}. Error: {str(e)}")
            
#             results = {}
            
#             # Process based on input type
#             if not self.input_text:
#                 raise ValueError("Input text is required when Text input type is selected")
            
#             processed_text, entities = processor.process_text(
#                 text=self.input_text,
#                 operator=self.operator
#             )
            
#             results["text"] = processed_text
            
#             if self.return_entities:
#                 results["entities"] = entities
            
#             # Return appropriate output
#             if len(results) == 1:
#                 return next(iter(results.values()))
#             else:
#                 return results
            
#         except Exception as e:
#             logger.error(f"Error processing PII: {e}")
#             raise

#     async def message_response(self) -> Message:
#         """Return processed text as a message response."""
#         try:
#             # Process the PII
#             result = await self.process_pii()
            
#             # Format the result as a message
#             if isinstance(result, str):
#                 message_content = result
#             elif isinstance(result, dict) and "text" in result:
#                 message_content = result["text"]
#             elif isinstance(result, dict) and "documents" in result:
#                 # Combine document page contents
#                 message_content = "\n\n".join([doc.page_content for doc in result["documents"]])
#             else:
#                 message_content = str(result)
            
#             # Create a simple message response
#             return Message(content=message_content, type="text")
        
#         except Exception as e:
#             logger.error(f"Error creating message response: {e}")
#             # Create more informative error message
#             error_msg = f"Error processing PII: {str(e)}\n"
            
#             if "SpaCy model" in str(e):
#                 error_msg += "\nIt appears there was an issue with the SpaCy model. Please ensure you have the required model installed."
#                 error_msg += "\nYou can install it manually with: python -m spacy download en_core_web_lg"
#             elif "HuggingFace" in str(e):
#                 error_msg += "\nIt appears there was an issue with the HuggingFace model. Please ensure you have the required dependencies installed."
            
#             return Message(content=error_msg, type="error")

#     async def to_toolkit(self) -> list[Tool]:
#         """Make the component available as a tool for agents."""
#         from langchain_core.tools import StructuredTool
        
#         async def presidio_pii_tool(text: str) -> str:
#             """Process text to detect and anonymize PII."""
#             try:
#                 # Set the input text
#                 self.input_text = text
#                 self.input_type = "Text"
                
#                 # Process the text
#                 result = await self.process_pii()
                
#                 # Return the processed text
#                 if isinstance(result, str):
#                     return result
#                 elif isinstance(result, dict) and "text" in result:
#                     return result["text"]
#                 else:
#                     return str(result)
#             except Exception as e:
#                 return f"Error processing PII: {str(e)}"
        
#         return [
#             StructuredTool.from_function(
#                 func=presidio_pii_tool,
#                 name="presidio_pii_processor",
#                 description="Detects and anonymizes personally identifiable information (PII) in text using Microsoft Presidio.",
#                 return_direct=True,
#                 args_schema=None  # Can define a schema if needed
#             )
#         ]

#     async def update_build_config(self, build_config: dotdict, field_value: str, field_name: str | None = None) -> dotdict:
#         """Update build configuration based on field changes."""
#         if field_name == "model_family":
#             # Update model name options based on selected family
#             if field_value == "spaCy":
#                 build_config["model_name"]["options"] = ["en_core_web_sm"]
#                 build_config["model_name"]["value"] = "en_core_web_lg"
#             elif field_value == "HuggingFace":
#                 build_config["model_name"]["options"] = ["HuggingFace/obi/deid_roberta_i2b2", "HuggingFace/StanfordAIMI/stanford-deidentifier-base"]
#                 build_config["model_name"]["value"] = "HuggingFace/obi/deid_roberta_i2b2"
        
#         return build_config


# class PresidioProcessor:
#     """A wrapper to use Presidio for PII detection and anonymization."""
    
#     def __init__(
#         self,
#         model_family: str = "spaCy",
#         model_name: str = "en_core_web_lg",
#         threshold: float = 0.4,
#         allow_list: List[str] = None,
#         deny_list: List[str] = None,
#     ):
#         """Initialize the processor.
        
#         Args:
#             model_family: NER model package ("spaCy" or "HuggingFace")
#             model_name: Model name within the package
#             threshold: Confidence threshold for entity detection
#             allow_list: List of words to be excluded from detection
#             deny_list: List of words to be included in detection
#         """
        
#         # Get NLP engine and registry
#         nlp_engine, registry = PresidioNlpEngineFactory.get_nlp_engine(model_family, model_name)
        
#         # Create analyzer
#         self.analyzer = AnalyzerEngine(
#             nlp_engine=nlp_engine,
#             registry=registry
#         )
        
#         # Create anonymizer
#         self.anonymizer = AnonymizerEngine()
        
#         # Store configuration
#         self.threshold = threshold
#         self.allow_list = allow_list or []
#         self.deny_list = deny_list or []
        
#         # Add deny list recognizer if provided
#         if self.deny_list:
#             deny_list_recognizer = PatternRecognizer(
#                 supported_entity="GENERIC_PII", 
#                 deny_list=self.deny_list
#             )
#             self.analyzer.registry.add_recognizer(deny_list_recognizer)
        
#         # Get supported entities
#         self.supported_entities = self.analyzer.get_supported_entities()
    
#     def analyze(self, text: str):
#         """Analyze text for PII entities."""
#         # Prepare analyze parameters
#         analyze_params = {
#             "text": text,
#             "entities": None,  # Detect all supported entities
#             "language": "en",
#             "score_threshold": self.threshold,
#             "allow_list": self.allow_list
#         }
        
#         # Analyze the text
#         results = self.analyzer.analyze(**analyze_params)
#         return results
    
#     def anonymize(
#         self, 
#         text: str, 
#         analyze_results, 
#         operator: str = "replace",
#         mask_char: str = "*",
#         number_of_chars: int = None,
#         encrypt_key: str = "WmZq4t7w!z%C&F)J"
#     ):
#         """Anonymize PII entities in text."""
#         # Configure operator
#         if operator == "mask":
#             operator_config = {
#                 "type": "mask",
#                 "masking_char": mask_char,
#                 "chars_to_mask": number_of_chars,
#                 "from_end": False,
#             }
#         elif operator == "encrypt":
#             operator_config = {"key": encrypt_key}
#         elif operator == "highlight":
#             operator_config = {"lambda": lambda x: x}
#             operator = "custom"  # highlight is implemented as custom
#         else:
#             operator_config = None
        
#         # Anonymize the text
#         result = self.anonymizer.anonymize(
#             text,
#             analyze_results,
#             operators={"DEFAULT": OperatorConfig(operator, operator_config)},
#         )
        
#         return result
    
#     def process_text(
#         self, 
#         text: str, 
#         operator: str = "replace",
#         mask_char: str = "*",
#         number_of_chars: int = None,
#         encrypt_key: str = "WmZq4t7w!z%C&F)J",
#     ):
#         """Process text for PII detection and anonymization."""
#         # Analyze the text
#         analyze_results = self.analyze(text)
        
#         # If no entities found, return original text
#         if not analyze_results:
#             return text, []
        
#         # Prepare result entities for return
#         entities = []
#         for result in analyze_results:
#             entity = result.to_dict()
#             entity["text"] = text[result.start:result.end]
#             entities.append(entity)
        
#         # If we just want to highlight, return the original text and entities
#         if operator == "highlight":
#             return text, entities
        
#         # For all other operators, anonymize the text
#         anonymized_result = self.anonymize(
#             text=text,
#             analyze_results=analyze_results,
#             operator=operator,
#             mask_char=mask_char,
#             number_of_chars=number_of_chars,
#             encrypt_key=encrypt_key
#         )
        
#         return anonymized_result.text, entities
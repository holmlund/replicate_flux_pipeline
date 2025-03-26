"""
title: Replicate Flux Pipeline
author: David Holmlund
author_url: https://github.com/holmlund
original_author: Akatsuki.Ryu
original_author_url: https://github.com/akatsuki-ryu
sponsor: Digitalist Open Tech
date: 2025-03-25
version: 1.2
license: MIT
description: Forked from Akatsuki.Ryu's Flux pipeline with added parameter support
requirements: pydantic, replicate==0.32.1
"""

import os
import logging
from difflib import get_close_matches
from typing import List, Dict, Union, Generator, Iterator, Optional
from urllib.parse import urlparse

import replicate
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

# Ordered according to schema x-order
AVAILABLE_ASPECT_RATIOS = [
    "custom",  # x-order: 2
    "1:1",
    "16:9",
    "3:2",
    "2:3",
    "4:5",
    "5:4",
    "9:16",
    "3:4",
    "4:3"
]

AVAILABLE_OUTPUT_FORMATS = [
    "webp",  # default
    "jpg",
    "png"
]

ALLOWED_IMAGE_FORMATS = [
    "jpeg",
    "jpg",
    "png",
    "gif",
    "webp"
]

def validate_image_url(url: str) -> bool:
    """
    Validate that the image URL points to an allowed image format.
    
    Args:
        url: The URL to validate
        
    Returns:
        bool: True if the URL is valid and points to an allowed image format
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
            
        # Check file extension
        path = parsed.path.lower()
        return any(path.endswith(f".{fmt}") for fmt in ALLOWED_IMAGE_FORMATS)
    except Exception:
        return False

def fuzzy_match(input_text: str, candidates: List[str], default: str) -> str:
    """
    Generic fuzzy matching function for aspect ratio and output format.
    
    Args:
        input_text: The input text to match
        candidates: List of valid candidates to match against
        default: Default value to return if no match is found
        
    Returns:
        The matched value or default if no match found
    """
    if not input_text or input_text.lower() == "none":
        return default
        
    input_lower = input_text.lower().strip()
    
    # Try exact match first
    if input_text in candidates:
        return input_text
        
    # Try fuzzy matching
    candidate_map = {c.lower(): c for c in candidates}
    matches = get_close_matches(input_lower, candidate_map.keys(), n=1, cutoff=0.6)
    
    if matches:
        return candidate_map[matches[0]]
        
    logger.warning(f"No matching value found for: {input_text}")
    return default

def convert_value(value: str) -> Union[str, bool, int]:
    """
    Convert string values to appropriate types.
    
    Args:
        value: The string value to convert
        
    Returns:
        The converted value (string, boolean, or integer)
    """
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.isdigit():
        return int(value)
    return value

def parse_command_params(user_message: str) -> Dict[str, Union[str, bool, int]]:
    """
    Parses command-line style parameters from the user message, expecting all parameters
    to be at the end of the message after the prompt.
    
    Args:
        user_message: The input message containing prompt and parameters
        
    Returns:
        A dictionary containing the prompt and any parsed parameters
        
    Example:
        >>> parse_command_params('A painting of a "sunset -- very beautiful" --aspect_ratio 16:9')
        {
            'prompt': 'A painting of a "sunset -- very beautiful"',
            'aspect_ratio': '16:9'
        }
    """
    try:
        # Find where the first parameter starts
        param_index = user_message.find('--')
        if param_index == -1:
            # No parameters, just the prompt
            return {"prompt": user_message.strip()}

        prompt_part = user_message[:param_index].strip()
        param_part = user_message[param_index:].strip()

        params = {"prompt": prompt_part}
        
        # Now parse param_part by space-splitting but being mindful that it starts with '--'
        tokens = param_part.split('--')[1:]  # skip the empty item before first --
        
        for tok in tokens:
            tok = tok.strip()
            if not tok:
                continue
            # 'aspect_ratio 16:9' -> param_name='aspect_ratio', value='16:9'
            pieces = tok.split(None, 1)
            param_name = pieces[0]
            if len(pieces) > 1:
                param_value = pieces[1]
            else:
                param_value = True

            # Convert if integer/bool
            param_value = convert_value(param_value)
            params[param_name] = param_value

        return params
    except Exception as e:
        logger.error(f"Error parsing command parameters: {str(e)}")
        return {"prompt": user_message.strip()}

class Pipeline:
    """
    A pipeline that calls Replicate's Flux model, allowing command-line style
    parameter input for aspect ratio, dimensions, and other parameters.
    """
    class Valves(BaseModel):
        REPLICATE_API_TOKEN: str

    def __init__(self):
        self.name = "Replicate Flux Pipeline"

        # Get API token from environment variable or valve configuration
        self.api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.valves = self.Valves(REPLICATE_API_TOKEN=self.api_token)

        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_TOKEN environment variable or valve configuration is required"
            )

        # Initialize Replicate client with explicit headers
        self.client = replicate.Client(
            headers={
                "User-Agent": "replicate-flux-pipeline/1.0.1",
                "Authorization": f"Token {self.api_token}"
            }
        )

    async def on_startup(self):
        """
        Called on application startup (if using an async framework).
        Refreshes client with the latest token from valves if available.
        """
        logger.info(f"on_startup: {__name__}")
        if self.valves.REPLICATE_API_TOKEN:
            self.api_token = self.valves.REPLICATE_API_TOKEN
            self.client = replicate.Client(
                headers={
                    "User-Agent": "replicate-flux-pipeline/1.0.1",
                    "Authorization": f"Token {self.api_token}"
                }
            )

    async def on_shutdown(self):
        """
        Called on application shutdown (if using an async framework).
        """
        logger.info(f"on_shutdown: {__name__}")

    def get_aspect_ratio_from_input(self, input_text: str) -> str:
        """Fuzzy-match the user's input text to an available aspect ratio."""
        return fuzzy_match(input_text, AVAILABLE_ASPECT_RATIOS, "1:1")

    def get_output_format_from_input(self, input_text: str) -> str:
        """Fuzzy-match the user's input text to an available output format."""
        return fuzzy_match(input_text, AVAILABLE_OUTPUT_FORMATS, "webp")

    def validate_dimensions(self, width: Optional[int], height: Optional[int]) -> tuple[Optional[int], Optional[int]]:
        """
        Validate and adjust image dimensions to be within Flux's constraints.
        """
        if width is None or height is None:
            return None, None
            
        # Ensure dimensions are within bounds
        width = max(256, min(1440, width))
        height = max(256, min(1440, height))
        
        # Round to nearest multiple of 32
        width = round(width / 32) * 32
        height = round(height / 32) * 32
        
        return width, height

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: Optional[List[dict]] = None,
        body: Optional[dict] = None
    ) -> Union[str, Generator, Iterator]:
        """
        Primary entry point for image generation.
        Extract command-line style params from the prompt and pass them to
        Replicate's 'black-forest-labs/flux-1.1-pro' model.
        
        Args:
            user_message: The user's input message containing prompt and parameters
            model_id: The model ID to use (currently unused as we only support flux-1.1-pro)
            messages: Optional list of previous messages (currently unused)
            body: Optional request body (currently unused)
            
        Returns:
            A string containing markdown-formatted image data or error message
        """
        logger.info(f"pipe: {__name__}")
        try:
            # 1) Parse command-line style params
            params = parse_command_params(user_message)
            
            # Validate required prompt
            if not params.get("prompt", "").strip():
                return "Error: Prompt is required"
                
            # Warn about unknown parameters
            known_params = {
                "prompt", "aspect_ratio", "width", "height", "seed", "image_prompt",
                "output_format", "output_quality", "safety_tolerance", "prompt_upsampling"
            }
            unknown_params = set(params.keys()) - known_params
            if unknown_params:
                logger.warning(f"Unknown parameters ignored: {unknown_params}")
            
            # 2) Prepare input params in schema order
            input_params = {
                "prompt": params.get("prompt", "").strip(),  # x-order: 0
                "aspect_ratio": self.get_aspect_ratio_from_input(params.get("aspect_ratio", "1:1")),  # x-order: 2
            }
            
            # Add image_prompt only if provided
            if "image_prompt" in params:
                image_prompt = params["image_prompt"]
                if not validate_image_url(image_prompt):
                    return "Error: image_prompt must be a valid URL pointing to a jpeg, png, gif, or webp image"
                input_params["image_prompt"] = image_prompt  # x-order: 1
            
            # Handle custom dimensions if aspect ratio is custom
            if input_params["aspect_ratio"] == "custom":
                width, height = self.validate_dimensions(
                    params.get("width"),
                    params.get("height")
                )
                if width and height:
                    input_params["width"] = width  # x-order: 3
                    input_params["height"] = height  # x-order: 4
            
            # Add remaining parameters in schema order
            if "seed" in params:
                input_params["seed"] = int(params["seed"])  # x-order: 6
            if "prompt_upsampling" in params:
                input_params["prompt_upsampling"] = bool(params["prompt_upsampling"])  # x-order: 7
            if "output_format" in params:
                input_params["output_format"] = self.get_output_format_from_input(params["output_format"])  # x-order: 8
            if "output_quality" in params:
                input_params["output_quality"] = min(100, max(0, params["output_quality"]))  # x-order: 9
            if "safety_tolerance" in params:
                input_params["safety_tolerance"] = min(6, max(1, params["safety_tolerance"]))  # x-order: 5

            logger.info(f"Final input params: {input_params}")

            # 3) Call the replicate model
            output = self.client.run("black-forest-labs/flux-1.1-pro", input=input_params)

            # 4) Handle the output
            if output:
                logger.info(f"Generated image URL: {output}")
                return f"![image]({output})\n"
            else:
                return "No image was generated."
                
        except Exception as e:
            logger.exception("Error generating image")
            return f"Error generating image: {str(e)}" 
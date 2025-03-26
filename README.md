# Replicate Flux Pipeline

A image generation pipeline for Open-Webui that integrates with Replicate's Flux 1.1 Pro API. This pipeline provides a flexible and intuitive way to generate high-quality images using command-line style parameters.

## Description

This project provides a Python-based pipeline that interfaces with Replicate's Flux API, offering a wide range of image generation capabilities. It supports various aspect ratios, custom dimensions, and image-to-image generation, making it versatile for different use cases:

- Multiple aspect ratio options (1:1, 16:9, 3:2, etc.)
- Custom dimension support with automatic validation
- Image-to-image generation with reference images
- Command-line style parameter input
- Automatic parameter matching with fuzzy search
- Markdown-formatted image output

## Features

- Command-line style parameter parsing with support for quoted strings
- Fuzzy matching for aspect ratios and output formats
- Comprehensive dimension validation and adjustment
- Robust error handling and parameter validation
- Markdown-formatted responses for Open-WebUI compatibility
- Support for image-to-image generation with reference images

## Installation

Add as a pipeline in Open-WebUI.

## Configuration

The pipeline requires a Replicate API token which can be configured in two ways:

- Environment variable: `REPLICATE_API_TOKEN`
- Valve configuration: `REPLICATE_API_TOKEN`

## Usage Examples

### Basic Usage
```
A beautiful sunset over mountains --aspect_ratio 16:9
```

### With Custom Dimensions
```
A city skyline at night --aspect_ratio custom --width 1024 --height 576
```

### With Image Prompt
```
A futuristic car --image_prompt https://example.com/reference.jpg
```

### Full Parameter Example
```
A magical forest --aspect_ratio 16:9 --seed 123 --output_format webp --output_quality 90 --safety_tolerance 3 --prompt_upsampling true
```

## Available Parameters

All parameters must be specified at the end of the prompt after the image description:

- `--prompt`: The text description of the image to generate (required)
- `--aspect_ratio`: Image aspect ratio (default: "1:1")
  - Available ratios: "1:1", "16:9", "3:2", "2:3", "4:5", "5:4", "9:16", "3:4", "4:3", "custom"
  - Use "custom" with `--width` and `--height` for specific dimensions
- `--width`: Custom width (required if aspect_ratio is "custom")
  - Range: 256-1440 pixels
  - Automatically rounded to nearest multiple of 32
- `--height`: Custom height (required if aspect_ratio is "custom")
  - Range: 256-1440 pixels
  - Automatically rounded to nearest multiple of 32
- `--seed`: Random seed for reproducible results
- `--image_prompt`: URL to a reference image (must be jpeg, png, gif, or webp)
- `--output_format`: Image format (default: "webp")
  - Available formats: "webp", "jpg", "png"
- `--output_quality`: Output quality (0-100, default: 80)
- `--safety_tolerance`: Safety filter tolerance (1-6, default: 3)
- `--prompt_upsampling`: Enable prompt upsampling (default: false)

## Response Format

The pipeline returns markdown-formatted strings:

- Success: `![image](https://replicate.delivery/...)`
- Error: `Error: <error message>`

## Dimension Handling

The pipeline supports both predefined aspect ratios and custom dimensions. When using custom dimensions:
- Values are automatically clamped between 256 and 1440 pixels
- Dimensions are rounded to the nearest multiple of 32
- Both width and height must be specified when using custom aspect ratio

## License

This project is licensed under the MIT License.

## Attribution

Forked from [Akatsuki.Ryu](https://github.com/akatsuki-ryu)'s original implementation.

This fork adds parameter support and maintainability while preserving the core functionality.

## Acknowledgments

- Sponsored by Digitalist Open Tech
- Built with Replicate's Flux 1.1 Pro API 
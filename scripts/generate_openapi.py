#!/usr/bin/env python3
"""
Generate OpenAPI specification from FastAPI app.

Usage:
    python scripts/generate_openapi.py [--output openapi.json]
"""
import json
import argparse
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from genpulse.app import create_api


def generate_openapi(output_path: str = "openapi.json"):
    """
    Generate OpenAPI JSON specification from the FastAPI app.
    
    Args:
        output_path: Path to save the OpenAPI JSON file.
    """
    app = create_api()
    openapi_schema = app.openapi()
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    
    print(f"✓ OpenAPI specification generated: {output_file.absolute()}")
    print(f"  Title: {openapi_schema.get('info', {}).get('title')}")
    print(f"  Version: {openapi_schema.get('info', {}).get('version')}")
    print(f"  Paths: {len(openapi_schema.get('paths', {}))}")


def main():
    parser = argparse.ArgumentParser(description="Generate OpenAPI specification")
    parser.add_argument(
        "--output",
        "-o",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    
    args = parser.parse_args()
    generate_openapi(args.output)


if __name__ == "__main__":
    main()

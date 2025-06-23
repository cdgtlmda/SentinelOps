#!/usr/bin/env python3
"""
Generate SVG diagrams from Mermaid markdown files.
This script reads Mermaid diagrams from the diagrams.md file and
generates individual SVG files for each diagram.
"""

import json
import os
import re
import subprocess
from pathlib import Path

# Configuration
ARCHITECTURE_DIR = Path(__file__).parent
DIAGRAMS_MD = ARCHITECTURE_DIR / "diagrams.md"
OUTPUT_DIR = ARCHITECTURE_DIR / "diagrams"
MMDC_PATH = "npx @mermaid-js/mermaid-cli"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_diagrams(markdown_path):
    """Extract Mermaid diagrams from a markdown file."""
    with open(markdown_path, "r") as f:
        content = f.read()

    # Find all mermaid code blocks
    pattern = r"```mermaid\n(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)

    # Find all section headers to use as filenames
    sections = re.findall(r"## (.*?)\n", content)

    # Map section headers to diagram content
    diagrams = {}
    for i, section in enumerate(sections):
        if i < len(matches):
            # Create a filename-friendly version of the section header
            filename = (
                section.lower().replace(" ", "-").replace("#", "").replace("&", "and")
            )
            diagrams[filename] = matches[i]

    return diagrams


def generate_svg(diagram_content, output_path):
    """Generate an SVG file from Mermaid diagram content."""
    # Create a temporary file for the diagram content
    tmp_path = f"/tmp/{os.path.basename(output_path)}.mmd"
    with open(tmp_path, "w") as f:
        f.write(diagram_content)

    # Run mmdc to generate the SVG
    command = f"{MMDC_PATH} -i {tmp_path} -o {output_path} -t neutral"

    try:
        subprocess.run(command, shell=True, check=True)
        print("Generated {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error generating {output_path}: {e}")
        return False
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    """Main function to generate all diagrams."""
    print("Extracting diagrams from {DIAGRAMS_MD}")
    diagrams = extract_diagrams(DIAGRAMS_MD)

    print("Found {len(diagrams)} diagrams")

    for name, content in diagrams.items():
        output_path = OUTPUT_DIR / f"{name}.svg"
        generate_svg(content, output_path)

    print("Done!")


if __name__ == "__main__":
    main()

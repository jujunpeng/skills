"""Algorithmic Art Skill

Generates algorithmic art using p5.js by creating parameterized JavaScript
code from templates and serving it through an HTML viewer.
"""

import json
import os
import re
import shutil
from pathlib import Path
from string import Template

SKILL_DIR = Path(__file__).parent
TEMPLATES_DIR = SKILL_DIR / "templates"
OUTPUT_DIR = SKILL_DIR / "output"


def load_template(name: str) -> str:
    """Load a template file by name."""
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {name}")
    return path.read_text(encoding="utf-8")


def generate_sketch(params: dict) -> str:
    """Generate a p5.js sketch from the generator template with given params.

    Args:
        params: Dictionary of parameters to inject into the template.
                Expected keys: seed, palette, density, speed, style

    Returns:
        Generated JavaScript code as a string.
    """
    # Personal note: I prefer warmer earthy tones and a slightly slower default speed
    defaults = {
        "seed": 42,
        "palette": ["#3d405b", "#81b29a", "#f2cc8f", "#e07a5f", "#f4f1de"],
        "density": 50,
        "speed": 0.6,
        "style": "flow",
    }
    defaults.update(params)

    template_src = load_template("generator_template.js")

    # Inject parameters as a config block prepended to the template
    config_block = "// Auto-generated configuration\n"
    config_block += f"const CONFIG = {json.dumps(defaults, indent=2)};\n\n"

    return config_block + template_src


def build_viewer(sketch_js: str, title: str = "Algorithmic Art") -> str:
    """Embed the sketch JavaScript into the HTML viewer template.

    Args:
        sketch_js: The p5.js sketch source code.
        title: Title to display in the viewer.

    Returns:
        Complete HTML document as a string.
    """
    viewer_src = load_template("viewer.html")

    # Replace placeholder comment with actual sketch code
    embedded = viewer_src.replace(
        "// SKETCH_PLACEHOLDER",
        sketch_js,
    ).replace("Algorithmic Art Viewer", title)

    return embedded


def save_output(html: str, filename: str = "sketch.html") -> Path:
    """Save the generated HTML to the output directory.

    Args:
        html: HTML content to save.
        filename: Output filename.

    Returns:
        Path to the saved file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / filename
    out_path.write_text(html, encoding="utf-8")
    return out_path


def run(params: dict | None = None) -> Path:
    """Main entry point for the algorithmic-art skill.

    Args:
        params: Optional generation parameters.

    Returns:
        Path to the generated HTML file.
    """
    params = params or {}
    sketch_js = generate_sketch(params)
    title = params.get("title", "Algorithmic Art")
    html = build_viewer(sketch_js, title=title)
    out_path = save_output(html, filename="sketch.html")
    print(f"Generated sketch saved to: {out_path}")
    return out_path


if __name__ == "_

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, List
import os
import random
import textwrap


class WojakMemeGenerator:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir

        # Scan for available templates
        self.templates = {
            "chad": [f for f in os.listdir(template_dir) if f.startswith("chad")],
            "virgin": [f for f in os.listdir(template_dir) if f.startswith("virgin")],
        }

        # Define text styling for each character type
        self.text_styles = {
            "chad": {
                "size": 36,
                "color": (0, 0, 0),
                "max_width": 25,  # words per line
            },
            "virgin": {
                "size": 24,
                "color": (0, 0, 0),
                "max_width": 35,  # words per line
            },
        }

        # Define template positions and sizes
        self.layout = {
            "canvas_size": (1200, 800),
            "left": {"image": (50, 100), "text_start": (50, 600)},
            "right": {"image": (600, 100), "text_start": (600, 600)},
        }

    def _select_template(self, template_type: str) -> str:
        """Randomly select a template from available options"""
        available_templates = self.templates[template_type]
        if not available_templates:
            raise Exception(
                f"No {template_type} templates found in {self.template_dir}"
            )
        return random.choice(available_templates)

    def _load_template(self, template_file: str) -> Image.Image:
        """Load and return the template image"""
        try:
            path = os.path.join(self.template_dir, template_file)
            img = Image.open(path).convert("RGBA")

            # Resize image to a reasonable height while maintaining aspect ratio
            target_height = 400
            aspect_ratio = img.width / img.height
            target_width = int(target_height * aspect_ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

            return img
        except FileNotFoundError:
            raise Exception(f"Template file {template_file} not found")

    def _add_text(
        self, image: Image.Image, text: str, position: Tuple[int, int], style: str
    ) -> Image.Image:
        """Add styled text to the image"""
        draw = ImageDraw.Draw(image)
        text_style = self.text_styles[style]

        # Use a default system font
        try:
            # Try to use Arial or a similar font if available
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                text_style["size"],
            )
        except OSError:
            try:
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Arial.ttf", text_style["size"]
                )
            except OSError:
                font = ImageFont.load_default()
                print("Warning: Using default font as system fonts not found")

        # Wrap text
        wrapped_text = textwrap.fill(text, width=text_style["max_width"])

        # Add text with outline for better readability
        outline_color = (255, 255, 255)
        outline_width = 2

        # Draw text outline
        for adj in range(-outline_width, outline_width + 1):
            for adj2 in range(-outline_width, outline_width + 1):
                if adj != 0 or adj2 != 0:
                    draw.text(
                        (position[0] + adj, position[1] + adj2),
                        wrapped_text,
                        font=font,
                        fill=outline_color,
                    )

        # Draw main text
        draw.text(position, wrapped_text, font=font, fill=text_style["color"])

        return image

    def generate_meme(
        self, chad_text: str, virgin_text: str, chad_side: str = "right"
    ) -> Image.Image:
        """Generate the complete Virgin vs Chad meme"""
        # Create base canvas (white background)
        canvas = Image.new("RGBA", self.layout["canvas_size"], (255, 255, 255, 255))

        # Select and load templates
        chad_template = self._select_template("chad")
        virgin_template = self._select_template("virgin")

        chad_img = self._load_template(chad_template)
        virgin_img = self._load_template(virgin_template)

        # Position images based on chad_side
        if chad_side == "right":
            canvas.paste(virgin_img, self.layout["left"]["image"], virgin_img)
            canvas.paste(chad_img, self.layout["right"]["image"], chad_img)

            # Add text
            canvas = self._add_text(
                canvas, virgin_text, self.layout["left"]["text_start"], "virgin"
            )
            canvas = self._add_text(
                canvas, chad_text, self.layout["right"]["text_start"], "chad"
            )
        else:
            canvas.paste(chad_img, self.layout["left"]["image"], chad_img)
            canvas.paste(virgin_img, self.layout["right"]["image"], virgin_img)

            # Add text
            canvas = self._add_text(
                canvas, chad_text, self.layout["left"]["text_start"], "chad"
            )
            canvas = self._add_text(
                canvas, virgin_text, self.layout["right"]["text_start"], "virgin"
            )

        return canvas


def main():
    generator = WojakMemeGenerator()

    # Example usage
    chad_text = "Embraces new technologies\nMasters multiple programming languages\nBuilds scalable solutions"
    virgin_text = "Afraid of learning new things\nOnly knows one language\nCopy-pastes from Stack Overflow"

    # Generate meme
    meme = generator.generate_meme(
        chad_text=chad_text, virgin_text=virgin_text, chad_side="right"  # or "left"
    )

    meme.save("virgin_vs_chad_meme.png")


if __name__ == "__main__":
    main()

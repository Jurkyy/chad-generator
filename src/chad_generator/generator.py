import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, List, Set
import os
import random
import textwrap
import openai


class WojakMemeGenerator:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir

        # Map matching templates
        self.template_pairs = self._map_template_pairs()

        # Target dimensions for consistency
        self.target_dimensions = (300, 400)  # height and width for figures

        # Define text positioning for surrounding text
        self.text_positions = {
            "virgin": [
                (0.2, 0.2, "top"),  # top left
                (0.1, 0.4, "left"),  # middle left
                (0.2, 0.6, "bottom"),  # bottom left
            ],
            "chad": [
                (0.7, 0.2, "top"),  # top right
                (0.8, 0.4, "right"),  # middle right
                (0.7, 0.6, "bottom"),  # bottom right
            ],
        }

    def _map_template_pairs(self) -> List[Tuple[str, str]]:
        """Map virgin and chad templates that should go together"""
        virgin_templates = sorted(
            [f for f in os.listdir(self.template_dir) if f.startswith("virgin")]
        )
        chad_templates = sorted(
            [f for f in os.listdir(self.template_dir) if f.startswith("chad")]
        )

        # Pair matching numbered templates
        return list(zip(virgin_templates, chad_templates))

    def _resize_template(self, img: Image.Image) -> Image.Image:
        """Resize image to target dimensions while maintaining aspect ratio"""
        aspect_ratio = img.width / img.height
        new_height = self.target_dimensions[0]
        new_width = int(new_height * aspect_ratio)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _generate_argument_points(self, topic: str, is_chad: bool) -> List[str]:
        """Generate appropriate points for either chad or virgin side"""
        # This is a simplified version - in practice, you'd want to use a more sophisticated
        # text generation approach, possibly with GPT-3 or similar

        chad_templates = [
            "Embraces {topic} fully",
            "Masters {topic} effortlessly",
            "Innovates with {topic}",
            "Leads others in {topic}",
            "Confident about {topic}",
        ]

        virgin_templates = [
            "Afraid of {topic}",
            "Struggles with basic {topic}",
            "Complains about {topic}",
            "Never truly understands {topic}",
            "Avoids {topic} completely",
        ]

        templates = chad_templates if is_chad else virgin_templates
        return [
            template.format(topic=topic) for template in random.sample(templates, 3)
        ]

    def _add_surrounding_text(
        self,
        image: Image.Image,
        texts: List[str],
        positions: List[Tuple[float, float, str]],
        is_chad: bool,
    ) -> Image.Image:
        """Add text surrounding the figure"""
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
            )
        except OSError:
            font = ImageFont.load_default()

        canvas_width, canvas_height = image.size

        for text, (x, y, align) in zip(texts, positions):
            x_pos = int(x * canvas_width)
            y_pos = int(y * canvas_height)

            # Add white outline for better readability
            outline_color = (255, 255, 255)
            text_color = (0, 0, 0)
            outline_width = 2

            for dx in [-outline_width, outline_width]:
                for dy in [-outline_width, outline_width]:
                    draw.text(
                        (x_pos + dx, y_pos + dy), text, font=font, fill=outline_color
                    )

            draw.text((x_pos, y_pos), text, font=font, fill=text_color)

        return image

    def generate_meme(self, topic: str, chad_side: str = "right") -> Image.Image:
        """Generate the complete Virgin vs Chad meme"""
        # Select a random template pair
        virgin_template, chad_template = random.choice(self.template_pairs)

        # Create base canvas
        canvas = Image.new("RGBA", (1200, 800), (255, 255, 255, 255))

        # Load and resize templates
        virgin_img = self._resize_template(
            Image.open(os.path.join(self.template_dir, virgin_template)).convert("RGBA")
        )
        chad_img = self._resize_template(
            Image.open(os.path.join(self.template_dir, chad_template)).convert("RGBA")
        )

        # Generate argument points
        chad_texts = self._generate_argument_points(topic, True)
        virgin_texts = self._generate_argument_points(topic, False)

        # Position images and text based on chad_side
        if chad_side == "right":
            # Paste images
            canvas.paste(virgin_img, (200, 200), virgin_img)
            canvas.paste(chad_img, (700, 200), chad_img)

            # Add surrounding text
            canvas = self._add_surrounding_text(
                canvas, virgin_texts, self.text_positions["virgin"], False
            )
            canvas = self._add_surrounding_text(
                canvas, chad_texts, self.text_positions["chad"], True
            )
        else:
            # Paste images
            canvas.paste(chad_img, (200, 200), chad_img)
            canvas.paste(virgin_img, (700, 200), virgin_img)

            # Add surrounding text
            canvas = self._add_surrounding_text(
                canvas, chad_texts, self.text_positions["virgin"], True
            )
            canvas = self._add_surrounding_text(
                canvas, virgin_texts, self.text_positions["chad"], False
            )

        return canvas


def main():
    generator = WojakMemeGenerator()

    # Example usage with a topic
    topic = "programming"

    # Generate meme with random chad/virgin side assignment
    chad_side = random.choice(["left", "right"])
    meme = generator.generate_meme(topic=topic, chad_side=chad_side)

    meme.save("virgin_vs_chad_meme2.png")


if __name__ == "__main__":
    main()

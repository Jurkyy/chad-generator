import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, List, Optional
import os
import random
import textwrap
import anthropic
from math import cos, sin, pi


class ArgumentGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.use_api = bool(api_key)
        if self.use_api:
            self.client = anthropic.Anthropic(api_key=api_key)

    def _wrap_text(self, text: str, max_chars: int = 25) -> str:
        """Wrap text to multiple lines if too long"""
        lines = textwrap.wrap(text, width=max_chars, break_long_words=False)
        return "\n".join(lines)

    def _format_point(self, point: str) -> str:
        """Format and wrap a point to fit the meme style"""
        point = point.lstrip("- *•").strip()
        wrapped = self._wrap_text(point)
        lines = wrapped.split("\n")
        lines[0] = f"• {lines[0]}"
        if len(lines) > 1:
            lines[1:] = [f"  {line}" for line in lines[1:]]
        return "\n".join(lines)

    def generate_points(
        self, topic_parts: Tuple[str, str], is_chad: bool, num_points: int = 5
    ) -> List[str]:
        """Generate exactly num_points points with consistent theming"""
        topic = topic_parts[1] if is_chad else topic_parts[0]

        if self.use_api:
            try:
                prompt = f"""Generate {num_points} contrasting bullet points for a Virgin vs Chad meme comparing {topic_parts[0]} vs {topic_parts[1]}.
                Focus on the {'chad/superior' if is_chad else 'virgin/inferior'} aspects of {topic} and only show me those {num_points}.

                Rules:
                - Each point must be under 40 characters
                - Embrace absurd, hyperbolic comparisons
                - Mix physical and behavioral traits
                - Include both serious and ridiculous elements
                - Focus on stereotypical extremes

                Example Comparison - Worker vs Unemployed:

                Virgin Worker:
                - Bags under eyes from overtime
                - Dead inside from meetings
                - Lives for weekend coffee breaks
                - No time for dating or hobbies
                - Corporate slave mentality

                Chad Unemployed:
                - Perfect skin from zero stress
                - Sleeps 12 hours like a king
                - Has time to master 5 hobbies
                - Government pays him to exist
                - Never touched a spreadsheet

                Format: Return only bullet points separated by newlines. No additional text or explanations.
                Keep each side's traits thematically connected to create a stronger contrast.
                """

                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}],
                )

                points = [
                    p.strip()
                    for p in response.content[0].text.strip().split("\n")
                    if p.strip()
                    and not p.strip().startswith("Here")
                    and not p.strip().endswith(":")  # Exclude headers
                    and p.strip().startswith("-")  # Only include bullet points
                ]

                # If you still want to enforce a length limit, you could do:
                points = [
                    p[2:].strip() for p in points
                ]  # Remove "- " from the beginning

                if len(points) != num_points:
                    return self._generate_themed_points(topic, is_chad, num_points)

                return [self._format_point(p) for p in points]

            except Exception as e:
                print(f"API generation failed: {e}")
                return self._generate_themed_points(topic, is_chad, num_points)

        return self._generate_themed_points(topic, is_chad, num_points)

    def _generate_themed_points(
        self, topic: str, is_chad: bool, num_points: int
    ) -> List[str]:
        """Generate exactly num_points thematically consistent points"""
        chad_templates = [
            f"{topic} feared by gods",
            f"Makes chads stronger",
            f"{topic} energy radiates",
            f"Never needs practice",
            f"Crushes competition",
            f"Has 300 IQ moves",
            f"Gigachad approves",
            f"Sigma {topic} grindset",
        ]

        virgin_templates = [
            f"Mom still buys {topic}",
            f"Scared of {topic} power",
            f"Needs {topic} manual",
            f"Everyone mocks him",
            f"Can't handle basics",
            f"Cries at {topic}",
            f"Zero skill level",
            f"Still uses training mode",
        ]

        templates = chad_templates if is_chad else virgin_templates
        selected = random.sample(templates, num_points)
        return [self._format_point(p) for p in selected]


class TextLayoutManager:
    def __init__(self, canvas_width: int, canvas_height: int, num_points: int = 5):
        self.width = canvas_width
        self.height = canvas_height
        self.num_points = num_points

        # Centers for the figures
        self.centers = {
            "virgin": (self.width * 0.35, self.height * 0.5),
            "chad": (self.width * 0.65, self.height * 0.5),
        }

        # Horizontal spread ranges
        self.spreads = {
            "virgin": (self.width * 0.05, self.width * 0.1),  # Left side spread
            "chad": (self.width * 0.7, self.width * 0.95),  # Right side spread
        }

    def get_positions(self, is_chad: bool) -> List[Tuple[int, int]]:
        """Get text positions spread out horizontally from the figure"""
        positions = []
        center = self.centers["chad" if is_chad else "virgin"]
        spread_range = self.spreads["chad" if is_chad else "virgin"]

        # Calculate vertical spacing
        total_height = 400  # Height range for text
        vertical_step = (
            total_height / (self.num_points - 1) if self.num_points > 1 else 0
        )
        base_y = center[1] - total_height / 2  # Start from above the center

        for i in range(self.num_points):
            # Alternate between left and right of the spread range
            x_offset = random.uniform(-30, 30)  # Small random horizontal variation
            if is_chad:
                x = spread_range[0] + x_offset
            else:
                x = spread_range[1] + x_offset

            # Add some random vertical variation
            y = base_y + (i * vertical_step) + random.uniform(-20, 20)

            positions.append((int(x), int(y)))

        return positions

    def calculate_text_bounds(
        self, text: str, position: Tuple[int, int], font
    ) -> Tuple[int, int, int, int]:
        """Calculate the bounding box for text"""
        left, top = position
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return (left, top, left + width, top + height)


class WojakMemeGenerator:
    def __init__(
        self,
        template_dir: str = "templates",
        api_key: Optional[str] = None,
        num_points: int = 5,
    ):
        self.template_dir = template_dir
        self.template_pairs = self._map_template_pairs()
        self.target_dimensions = (400, 500)
        self.canvas_size = (1600, 1000)
        self.argument_generator = ArgumentGenerator(api_key)
        self.layout_manager = TextLayoutManager(*self.canvas_size, num_points)

    def _map_template_pairs(self) -> List[Tuple[str, str]]:
        """Map virgin and chad templates that should go together"""
        virgin_templates = sorted(
            [f for f in os.listdir(self.template_dir) if f.startswith("virgin")]
        )
        chad_templates = sorted(
            [f for f in os.listdir(self.template_dir) if f.startswith("chad")]
        )
        return list(zip(virgin_templates, chad_templates))

    def _resize_template(self, img: Image.Image) -> Image.Image:
        """Resize image to target dimensions while maintaining aspect ratio"""
        aspect_ratio = img.width / img.height
        new_height = self.target_dimensions[1]
        new_width = int(new_height * aspect_ratio)
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _add_text_with_outline(
        self,
        draw: ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        is_title: bool = False,
    ) -> None:
        """Add text with outline for better readability"""
        x, y = position
        outline_color = (255, 255, 255)
        text_color = (0, 0, 0)
        outline_width = 3

        if is_title:
            font = font.font_variant(size=40)

        lines = text.split("\n")
        bbox = font.getbbox("A")
        line_height = bbox[3] - bbox[1] + 5

        for i, line in enumerate(lines):
            line_y = y + (i * line_height)

            # Draw outline
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    draw.text(
                        (x + dx, line_y + dy), line, font=font, fill=outline_color
                    )

            # Draw main text
            draw.text((x, line_y), line, font=font, fill=text_color)

    def generate_meme(self, topic: str, virgin_side: str = "left") -> Image.Image:
        """Generate the complete Virgin vs Chad meme

        Args:
            topic (str): Input in format "X vs Y"
            virgin_side (str): Which side the virgin should be on ("left" or "right")
                            Default is "left"

        Returns:
            Image.Image: Generated meme image
        """
        canvas = Image.new("RGBA", self.canvas_size, (255, 255, 255, 255))

        # Split the topic into two parts
        topic_parts = topic.split(" vs ")
        if len(topic_parts) != 2:
            print("check splitting of topic, couldn't parse this input properly")
            topic_parts = (topic, topic)
            print(topic_parts)
            return 0

        # Determine which topic goes on which side based on virgin_side parameter
        if virgin_side.lower() == "right":
            chad_topic, virgin_topic = topic_parts
        else:  # default to virgin on left
            virgin_topic, chad_topic = topic_parts

        # Get templates
        virgin_template, chad_template = random.choice(self.template_pairs)

        # Load and resize images
        virgin_img = self._resize_template(
            Image.open(os.path.join(self.template_dir, virgin_template)).convert("RGBA")
        )
        chad_img = self._resize_template(
            Image.open(os.path.join(self.template_dir, chad_template)).convert("RGBA")
        )

        chad_points = self.argument_generator.generate_points(
            topic_parts, True, self.layout_manager.num_points
        )
        virgin_points = self.argument_generator.generate_points(
            topic_parts, False, self.layout_manager.num_points
        )

        draw = ImageDraw.Draw(canvas)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
            )
        except OSError:
            font = ImageFont.load_default()

        # Position images
        virgin_x = int(self.canvas_size[0] * 0.35 - virgin_img.width / 2)
        chad_x = int(self.canvas_size[0] * 0.65 - chad_img.width / 2)

        canvas.paste(virgin_img, (virgin_x, 250), virgin_img)
        canvas.paste(chad_img, (chad_x, 250), chad_img)

        # Add centered titles
        virgin_title = f"The Virgin {topic_parts[0]}"
        chad_title = f"The Chad {topic_parts[1]}"

        virgin_bbox = font.getbbox(virgin_title)
        chad_bbox = font.getbbox(chad_title)
        virgin_title_width = virgin_bbox[2] - virgin_bbox[0]
        chad_title_width = chad_bbox[2] - chad_bbox[0]

        virgin_title_x = virgin_x + virgin_img.width // 4 - virgin_title_width // 2
        chad_title_x = chad_x + chad_img.width // 4 - chad_title_width // 2

        self._add_text_with_outline(
            draw, virgin_title, (virgin_title_x, 100), font, True
        )
        self._add_text_with_outline(draw, chad_title, (chad_title_x, 100), font, True)

        # Add points with new positioning
        virgin_positions = self.layout_manager.get_positions(False)
        chad_positions = self.layout_manager.get_positions(True)

        for point, pos in zip(virgin_points, virgin_positions):
            self._add_text_with_outline(draw, point, pos, font)

        for point, pos in zip(chad_points, chad_positions):
            self._add_text_with_outline(draw, point, pos, font)

        return canvas


def _main_io_handling(topic, virgin_side):
    # You'll need to provide your Anthropic API key
    api_key = os.environ["ANTHROPIC_API_KEY"]
    generator = WojakMemeGenerator(api_key=api_key)

    # Generate filename from topic
    safe_filename = "_".join(topic.lower().replace(" vs ", "_vs_").split())
    output_filename = f"res/virgin_vs_chad_meme_{safe_filename}.png"

    # Generate and save the meme
    print(f"\nGenerating meme...")
    meme = generator.generate_meme(topic, virgin_side)
    meme.save(output_filename)
    print(f"Meme saved as: {output_filename}")


def main():
    # Get topic from user
    print("Enter your comparison in the format 'X vs Y':")
    topic = input("> ").strip()

    # Get side preference
    while True:
        print("\nWhich side should be the 'Virgin'?")
        print("1. Left side")
        print("2. Right side")
        print("3. Generate both sides")
        choice = input("Enter 1, 2 or 3: ").strip()

        if choice == "1":
            _main_io_handling(topic, "left")
            break
        elif choice == "2":
            _main_io_handling(topic, "right")
            break
        elif choice == "3":
            _main_io_handling(topic, "right")
            _main_io_handling(topic, "left")
            break
        else:
            print("Invalid choice. Please enter 1, 2 or 3.")


if __name__ == "__main__":
    main()

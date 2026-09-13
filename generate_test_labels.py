"""One-time setup script using Pillow to generate mock sample alcohol label images."""
import os
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent / "static" / "samples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WARNING_BODY = (
    "(1) According to the Surgeon General, women should not drink alcoholic "
    "beverages during pregnancy because of the risk of birth defects. (2) Consumption "
    "of alcoholic beverages impairs your ability to drive a car or operate machinery, "
    "and may cause health problems."
)


def get_fonts():
    font_bold_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    font_reg_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    try:
        title_font = ImageFont.truetype(font_bold_path, 34)
        sub_font = ImageFont.truetype(font_reg_path, 22)
        body_font = ImageFont.truetype(font_reg_path, 18)
        warn_title_font_bold = ImageFont.truetype(font_bold_path, 14)
        warn_title_font_plain = ImageFont.truetype(font_reg_path, 14)
        warn_body_font = ImageFont.truetype(font_reg_path, 14)
    except Exception:
        try:
            title_font = ImageFont.truetype("Arial", 34)
            sub_font = ImageFont.truetype("Arial", 22)
            body_font = ImageFont.truetype("Arial", 18)
            warn_title_font_bold = ImageFont.truetype("Arial-Bold", 14)
            warn_title_font_plain = ImageFont.truetype("Arial", 14)
            warn_body_font = ImageFont.truetype("Arial", 14)
        except Exception:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            warn_title_font_bold = ImageFont.load_default()
            warn_title_font_plain = ImageFont.load_default()
            warn_body_font = ImageFont.load_default()
    return {
        "title": title_font,
        "sub": sub_font,
        "body": body_font,
        "warn_bold": warn_title_font_bold,
        "warn_plain": warn_title_font_plain,
        "warn_body": warn_body_font,
    }


def draw_label(
    filename: str,
    brand_name: str,
    class_type: str,
    alcohol_content: str,
    net_contents: str,
    bottler: str,
    country: str | None = None,
    warning_title: str = "GOVERNMENT WARNING:",
    warning_title_bold: bool = True,
):
    width, height = 700, 520
    img = Image.new("RGB", (width, height), color="#FAF7F2")
    draw = ImageDraw.Draw(img)
    fonts = get_fonts()

    # Outer border
    draw.rectangle([15, 15, width - 15, height - 15], outline="#333333", width=3)
    draw.rectangle([22, 22, width - 22, height - 22], outline="#888888", width=1)

    y = 45

    # Brand Name
    draw.text((width / 2, y), brand_name, fill="#1A1A1A", font=fonts["title"], anchor="mm")
    y += 50

    # Class / Type
    draw.text((width / 2, y), class_type, fill="#4A4A4A", font=fonts["sub"], anchor="mm")
    y += 45

    # ABV & Net Contents
    details = f"{alcohol_content}  -  {net_contents}"
    draw.text((width / 2, y), details, fill="#222222", font=fonts["body"], anchor="mm")
    y += 35

    # Bottler
    draw.text((width / 2, y), bottler, fill="#333333", font=fonts["body"], anchor="mm")
    y += 30

    # Country of origin if present
    if country:
        draw.text((width / 2, y), f"Product of {country}", fill="#333333", font=fonts["body"], anchor="mm")
        y += 35
    else:
        y += 10

    # Divider line before government warning
    draw.line([(40, y), (width - 40, y)], fill="#CCCCCC", width=1)
    y += 15

    # Government Warning Box
    warn_title_font = fonts["warn_bold"] if warning_title_bold else fonts["warn_plain"]
    body_font = fonts["warn_body"]
    start_x = 40
    line_spacing = 20

    # Render first line with distinct warning title font followed by body text
    title_text = f"{warning_title} "
    title_box = draw.textbbox((start_x, y), title_text, font=warn_title_font)
    title_width = title_box[2] - title_box[0]

    # Measure how much body text fits on line 1 alongside the title
    max_line_width = width - 80
    remaining_line_width = max_line_width - title_width

    words = WARNING_BODY.split()
    line1_words = []
    word_idx = 0
    while word_idx < len(words):
        test_line = " ".join(line1_words + [words[word_idx]])
        bbox = draw.textbbox((0, 0), test_line, font=body_font)
        if (bbox[2] - bbox[0]) <= remaining_line_width:
            line1_words.append(words[word_idx])
            word_idx += 1
        else:
            break

    # Draw heading
    draw.text((start_x, y), title_text, fill="#1A1A1A", font=warn_title_font)
    # Draw rest of line 1
    line1_body = " ".join(line1_words)
    draw.text((start_x + title_width, y), line1_body, fill="#2A2A2A", font=body_font)
    y += line_spacing

    # Wrap and draw the remaining body text lines
    remaining_text = " ".join(words[word_idx:])
    wrapped_lines = textwrap.wrap(remaining_text, width=82)
    for line in wrapped_lines:
        draw.text((start_x, y), line, fill="#2A2A2A", font=body_font)
        y += line_spacing

    out_path = OUTPUT_DIR / filename
    img.save(out_path, "JPEG", quality=92)
    print(f"Generated: {out_path}")


def main():
    # 1. clean_pass
    draw_label(
        filename="1_all_fields_match_pass.jpg",
        brand_name="OLD TOM DISTILLERY",
        class_type="Kentucky Straight Bourbon Whiskey",
        alcohol_content="45% Alc./Vol. (90 Proof)",
        net_contents="750 mL",
        bottler="Bottled by Old Tom Distilling Co., Louisville, KY",
        country=None,
        warning_title="GOVERNMENT WARNING:",
        warning_title_bold=True,
    )

    # 2. brand_case_diff
    draw_label(
        filename="2_brand_name_case_difference_pass.jpg",
        brand_name="STONE'S THROW",
        class_type="American Dry Gin",
        alcohol_content="47% Alc./Vol.",
        net_contents="750 mL",
        bottler="Distilled by Stone's Throw Spirits, Portland, OR",
        country=None,
        warning_title="GOVERNMENT WARNING:",
        warning_title_bold=True,
    )

    # 3. warning_format_violation (title case, not bold)
    draw_label(
        filename="3_warning_not_bold_caps_fail.jpg",
        brand_name="BLUE RIDGE RYE",
        class_type="Straight Rye Whiskey",
        alcohol_content="46% Alc./Vol.",
        net_contents="750 mL",
        bottler="Blue Ridge Distilling Co., Asheville, NC",
        country=None,
        warning_title="Government Warning:",
        warning_title_bold=False,
    )

    # 4. abv_format_diff
    draw_label(
        filename="4_alcohol_proof_format_pass.jpg",
        brand_name="PRAIRIE HARVEST",
        class_type="Vodka",
        alcohol_content="40% Alc./Vol.",
        net_contents="750 mL",
        bottler="Prairie Harvest Distilling, Omaha, NE",
        country=None,
        warning_title="GOVERNMENT WARNING:",
        warning_title_bold=True,
    )

    # 5. missing_country_of_origin
    draw_label(
        filename="5_import_missing_country_fail.jpg",
        brand_name="HIGHLAND RESERVE",
        class_type="Single Malt Scotch Whisky",
        alcohol_content="43% Alc./Vol.",
        net_contents="700 mL",
        bottler="Highland Distillers Ltd., Edinburgh, Scotland",
        country="Scotland",
        warning_title="GOVERNMENT WARNING:",
        warning_title_bold=True,
    )

    # 6. genuine_mismatch
    draw_label(
        filename="6_brand_name_mismatch_fail.jpg",
        brand_name="OAK & IRON RUM",
        class_type="Dark Rum",
        alcohol_content="40% Alc./Vol.",
        net_contents="750 mL",
        bottler="Oak & Iron Distilling Co., Tampa, FL",
        country=None,
        warning_title="GOVERNMENT WARNING:",
        warning_title_bold=True,
    )


if __name__ == "__main__":
    main()

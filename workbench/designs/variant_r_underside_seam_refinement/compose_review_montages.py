"""Compose labeled contact sheets from the deterministic Snapshot outputs."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
REVIEW = (
    ROOT
    / "build/workbench/variant_r_underside_seam_refinement/review"
)
STAMP = "20260723T190142Z"
LABELS = ("Earlier flat-bottom", "Current spliced", "Candidate no-splice")


def _font(size: int):
    path = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    return ImageFont.truetype(str(path), size) if path.is_file() else ImageFont.load_default()


def _compose(kind: str, output_name: str) -> None:
    paths = (
        REVIEW / f"earlier-{kind}-lower-front_{STAMP}.png",
        REVIEW / f"current-{kind}-lower-front_{STAMP}.png",
        REVIEW / f"candidate-{kind}-lower-front_{STAMP}.png",
    )
    images = [Image.open(path).convert("RGB") for path in paths]
    tile_size = (800, 600)
    title_height = 62
    canvas = Image.new(
        "RGB",
        (tile_size[0] * len(images), tile_size[1] + title_height),
        "#eef3f9",
    )
    draw = ImageDraw.Draw(canvas)
    font = _font(28)
    for index, (label, image) in enumerate(zip(LABELS, images)):
        tile = image.resize(tile_size, Image.Resampling.LANCZOS)
        x_value = index * tile_size[0]
        canvas.paste(tile, (x_value, title_height))
        bounds = draw.textbbox((0, 0), label, font=font)
        text_width = bounds[2] - bounds[0]
        draw.text(
            (x_value + (tile_size[0] - text_width) / 2, 15),
            label,
            fill="#17212b",
            font=font,
        )
    canvas.save(REVIEW / output_name, optimize=True)


def main() -> None:
    _compose("smooth", "matched-smooth-lower-front.png")
    _compose("edge-overlay", "matched-edge-overlay-lower-front.png")


if __name__ == "__main__":
    main()

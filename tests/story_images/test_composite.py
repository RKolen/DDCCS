"""Unit tests for grounding pasted figures in src.story_images.composite."""

from typing import Tuple

from PIL import Image, ImageDraw

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

composite = import_module("src.story_images.composite")

DARK_BLUE = (10, 14, 30, 255)
PURPLE = (150, 70, 200, 255)


def _figure(colour: tuple, size: tuple = (40, 100)) -> Image.Image:
    """A solid opaque block on a transparent canvas, standing on the bottom.

    Args:
        colour: RGBA fill.
        size: Canvas (width, height).

    Returns:
        The RGBA cutout.
    """
    figure = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(figure).rectangle((10, 0, size[0] - 11, size[1] - 1), fill=colour)
    return figure


def _rgba(image: Image.Image, xy: Tuple[int, int]) -> Tuple[int, ...]:
    """One pixel as a tuple, narrowed from what Pillow may return.

    Args:
        image: An RGBA image.
        xy: The pixel.

    Returns:
        Its channel values.
    """
    pixel = image.getpixel(xy)
    assert isinstance(pixel, tuple), pixel
    return pixel


def test_a_figure_dims_towards_a_dark_scene_and_keeps_its_hue() -> None:
    """Studio light is taken down in a night scene, without a hue shift.

    Matching each channel separately turned a purple skin green against a
    dark alley, and borrowing the alley's colour cast turned it grey.
    """
    print("\n[TEST] match_light - dims, keeps hue")
    scene = Image.new("RGBA", (200, 200), DARK_BLUE)
    lit = composite.match_light(_figure(PURPLE), scene, (50, 50))
    red, green, blue, alpha = _rgba(lit, (20, 50))
    assert red + green + blue < sum(PURPLE[:3]), (red, green, blue)
    # One gain for all three channels: the ratios, and so the hue, survive.
    assert abs(red / blue - PURPLE[0] / PURPLE[2]) < 0.03, (red, green, blue)
    assert abs(green / blue - PURPLE[1] / PURPLE[2]) < 0.03, (red, green, blue)
    assert alpha == 255 and _rgba(lit, (2, 50))[3] == 0
    print(f"  [OK] {PURPLE[:3]} -> {(red, green, blue)}, still purple")


def test_a_scene_like_the_figure_leaves_it_alone() -> None:
    """Nothing to match means nothing changes."""
    print("\n[TEST] match_light - matching scene")
    scene = Image.new("RGBA", (200, 200), PURPLE)
    lit = composite.match_light(_figure(PURPLE), scene, (50, 50))
    # Close rather than exact: the lookup table rounds every level down.
    assert all(abs(a - b) <= 6 for a, b in zip(_rgba(lit, (20, 50)), PURPLE))
    print("  [OK] Colour within rounding")


def test_the_contact_shadow_sits_under_the_feet() -> None:
    """The ground darkens where the feet land, and nowhere near the head."""
    print("\n[TEST] cast_contact_shadow - placement")
    grey = (120, 120, 120, 255)
    scene = Image.new("RGBA", (200, 200), grey)
    composite.cast_contact_shadow(scene, _figure(PURPLE), (80, 50))
    feet = _rgba(scene, (100, 150))
    assert feet[0] < grey[0], feet
    assert _rgba(scene, (100, 60)) == grey
    assert _rgba(scene, (10, 150)) == grey
    print(f"  [OK] Ground at the feet {grey[0]} -> {feet[0]}; head and far side untouched")


def test_soften_edge_feathers_only_the_outline() -> None:
    """The cut line goes soft; the body stays solid."""
    print("\n[TEST] soften_edge")
    soft = composite.soften_edge(_figure(PURPLE))
    assert _rgba(soft, (20, 50))[3] == 255
    assert 0 < _rgba(soft, (10, 50))[3] < 255, _rgba(soft, (10, 50))
    print("  [OK] Interior opaque, edge partial")


def run_all_tests() -> None:
    """Run every compositing test."""
    test_a_figure_dims_towards_a_dark_scene_and_keeps_its_hue()
    test_a_scene_like_the_figure_leaves_it_alone()
    test_the_contact_shadow_sits_under_the_feet()
    test_soften_edge_feathers_only_the_outline()
    print("\n[PASS] All compositing tests passed.")


if __name__ == "__main__":
    run_all_tests()

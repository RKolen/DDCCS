"""Unit tests for src.story_images.regions."""

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

regions = import_module("src.story_images.regions")
lay_out = regions.lay_out
height_factor = regions.height_factor
ShotPerson = import_module("src.story_images.types").ShotPerson

CANVAS = (1152, 768)


def _cast() -> list:
    """Build a mixed-height party from the Example Campaign world."""
    return [
        ShotPerson(name="Frodo Baggins", appearance="Halfling, Rogue"),
        ShotPerson(name="Aragorn", appearance="Human, Ranger"),
        ShotPerson(name="Gandalf the Grey", appearance="Human, Wizard"),
    ]


def test_height_factor_reads_species_from_appearance() -> None:
    """A species word in the tags sets relative height."""
    print("\n[TEST] height_factor - species")
    assert height_factor(ShotPerson(name="A", appearance="Halfling, Druid")) < 1.0
    assert height_factor(ShotPerson(name="B", appearance="Dragonborn, Fighter")) > 1.0
    assert height_factor(ShotPerson(name="C", appearance="Human, Wizard")) == 1.0
    print("  [OK] Short, tall, and default")


def test_lay_out_puts_everyone_on_one_ground_line() -> None:
    """Figures share a floor, so a short one reads short and not distant."""
    print("\n[TEST] lay_out - shared ground line")
    placed = lay_out(_cast(), *CANVAS)
    assert len({region.bottom for region in placed}) == 1
    print("  [OK] One floor")


def test_lay_out_scales_a_halfling_below_a_human() -> None:
    """Height comes from the box, not from a word the model may ignore."""
    print("\n[TEST] lay_out - relative heights")
    placed = {region.name: region for region in lay_out(_cast(), *CANVAS)}
    assert placed["Frodo Baggins"].height < placed["Aragorn"].height
    print("  [OK] Halfling shorter than human")


def test_lay_out_keeps_regions_inside_the_canvas() -> None:
    """A region that ran off the edge would inpaint outside the image."""
    print("\n[TEST] lay_out - bounds")
    width, height = CANVAS
    for region in lay_out(_cast() * 3, width, height, "medium"):
        assert region.left >= 0 and region.top >= 0
        assert region.right <= width, f"{region.name} runs past the right edge"
        assert region.bottom <= height, f"{region.name} runs past the bottom"
    print("  [OK] Nine regions all within bounds")


def test_lay_out_without_people_is_empty() -> None:
    """No cast means no regions, not one covering the whole frame."""
    print("\n[TEST] lay_out - empty cast")
    assert lay_out([], *CANVAS) == []
    print("  [OK] Empty list")


def test_depth_makes_a_figure_smaller_and_higher() -> None:
    """Distance is height and floor together, not height alone.

    Scaling only the height turns a distant person into a short one standing
    at your feet. Both recede toward the horizon by the same factor.
    """
    print("\n[TEST] lay_out - depth reads as distance")
    cast = _cast()[:1]
    near = lay_out(cast, *CANVAS, "full",
                   [regions.Placement(cast[0].name, 0.5, 1.0)])[0]
    far = lay_out(cast, *CANVAS, "full",
                  [regions.Placement(cast[0].name, 0.5, 2.0)])[0]
    assert far.height < near.height, (near.height, far.height)
    assert far.bottom < near.bottom, (near.bottom, far.bottom)
    print(f"  [OK] {near.height}px at the front, {far.height}px at depth 2, "
          f"feet {near.bottom} -> {far.bottom}")


def test_lateral_places_the_figure_across_the_frame() -> None:
    """0 is the left edge, 1 the right, measured at the figure's centre."""
    print("\n[TEST] lay_out - lateral")
    cast = _cast()[:1]
    left = lay_out(cast, *CANVAS, "full", [regions.Placement(cast[0].name, 0.0)])[0]
    right = lay_out(cast, *CANVAS, "full", [regions.Placement(cast[0].name, 1.0)])[0]
    assert left.left == 0, left.left
    assert right.right == CANVAS[0], right.right
    print("  [OK] Clamped inside the frame at both extremes")


def test_defaults_reproduce_the_even_row() -> None:
    """No staging given is exactly the layout that existed before it.

    Every scene rendered so far used the even row; changing what it does
    silently would move figures in renders nobody asked to restage.
    """
    print("\n[TEST] lay_out - default staging unchanged")
    cast = _cast()
    assert lay_out(cast, *CANVAS) == lay_out(
        cast, *CANVAS, "full", regions.default_placements(cast)
    )
    print("  [OK] Defaults match the explicit even row")


def test_placement_is_clamped_to_the_frame_and_scene() -> None:
    """Out-of-range staging cannot push a figure off-canvas or inside out."""
    print("\n[TEST] Placement.clamped")
    wild = regions.Placement("A", lateral=5.0, depth=-3.0).clamped()
    assert wild.lateral == 1.0 and wild.depth == regions.NEAR_DEPTH
    far = regions.Placement("A", lateral=-1.0, depth=99.0).clamped()
    assert far.lateral == 0.0 and far.depth == regions.FAR_DEPTH
    print("  [OK] Lateral and depth held inside their limits")


def test_the_nearest_figure_is_painted_last() -> None:
    """Depth decides who wins an overlap, not who was ticked last.

    `place` pastes in sequence, so the final figure is drawn on top. The
    order was cast order, which let a character staged at the back be pasted
    over one at the front at a fraction of their height. The console numbers
    the cast front to back off the same rule, so a 1 has to come out whole.
    """
    print("\n[TEST] paint_order - furthest first")
    render = import_module("src.story_images.region_render")
    regions_mod = import_module("src.story_images.regions")

    def box(name: str) -> object:
        return regions_mod.Region(name=name, left=0, top=0, width=10, height=10)

    # Cast order puts the furthest last, which is exactly the wrong way up.
    cutouts = [
        (0, 1.0, 0, box("Aragorn"), b"near"),
        (0, 2.5, 1, box("Frodo Baggins"), b"far"),
        (0, 1.6, 2, box("Gandalf the Grey"), b"middle"),
    ]
    order = [region.name for region, _ in render.paint_order(cutouts)]
    assert order == ["Frodo Baggins", "Gandalf the Grey", "Aragorn"], order

    # Two at the same distance keep the order the cast was given in.
    tied = [
        (0, 2.0, 1, box("Tobias Stone"), b"b"),
        (0, 2.0, 0, box("Barliman Butterbur"), b"a"),
    ]
    assert [r.name for r, _ in render.paint_order(tied)] == [
        "Barliman Butterbur", "Tobias Stone"]
    print("  [OK] Furthest first, cast order breaks ties")


def test_an_operator_number_outranks_depth() -> None:
    """A small character at the back must be able to win an overlap.

    Depth also sets apparent size, and apparent size is not distance here -
    a halfling at the front of the scene is still smaller than an orc at the
    back. Dragging the small one forward to stop them being swallowed made
    everybody else's distance wrong, so who is in front is its own control.
    """
    print("\n[TEST] paint_order - a typed number beats depth")
    render = import_module("src.story_images.region_render")
    regions_mod = import_module("src.story_images.regions")

    def box(name: str) -> object:
        return regions_mod.Region(name=name, left=0, top=0, width=10, height=10)

    # The halfling stands furthest back and is still painted last.
    cutouts = [
        (2, 1.0, 0, box("Aragorn"), b"a"),
        (1, 2.8, 1, box("Frodo Baggins"), b"b"),
        (3, 1.4, 2, box("Gandalf the Grey"), b"c"),
    ]
    order = [region.name for region, _ in render.paint_order(cutouts)]
    assert order == ["Gandalf the Grey", "Aragorn", "Frodo Baggins"], order

    # Nobody numbered falls back to depth, behind everyone who is numbered.
    mixed = [
        (0, 1.0, 0, box("Tobias Stone"), b"a"),
        (1, 2.9, 1, box("Barliman Butterbur"), b"b"),
    ]
    assert [r.name for r, _ in render.paint_order(mixed)] == [
        "Tobias Stone", "Barliman Butterbur"]
    print("  [OK] The number wins; unnumbered falls back to depth")


def run_all_tests() -> None:
    """Run all region-layout tests."""
    test_height_factor_reads_species_from_appearance()
    test_lay_out_puts_everyone_on_one_ground_line()
    test_lay_out_scales_a_halfling_below_a_human()
    test_lay_out_keeps_regions_inside_the_canvas()
    test_lay_out_without_people_is_empty()
    test_depth_makes_a_figure_smaller_and_higher()
    test_lateral_places_the_figure_across_the_frame()
    test_defaults_reproduce_the_even_row()
    test_placement_is_clamped_to_the_frame_and_scene()
    test_the_nearest_figure_is_painted_last()
    test_an_operator_number_outranks_depth()
    print("\n[PASS] All region-layout tests passed.")


if __name__ == "__main__":
    run_all_tests()

# Tests for the M-D slice (M-2: addSprite without draw() side effect,
# M-3: fresh transformedPointlist in checkPolygonCollision).

from util.vector2d import Vector2d
from badies import Rock


def _set_shape(rock, shape_idx, scale):
    # Deterministic shape: rebuild the pointlist for the given outline.
    rock.rockShape = shape_idx
    rock.pointlist = [rock.scale(p, scale) for p in rock.createPointList()]


def test_add_sprite_does_not_call_draw(game):
    # M-2: adding a sprite must not invoke draw() (which used to render
    # the sprite to the screen and pin the transform at add-time).
    rock = Rock(game.stage, Vector2d(50, 50), Rock.largeRockType)
    calls = []
    original = rock.draw

    def spy():
        calls.append(1)
        return original()

    rock.draw = spy
    game.stage.addSprite(rock)
    assert calls == []
    assert rock in game.stage.spriteList


def test_add_sprite_sets_fresh_bounding_rect(game):
    # Use an explicitly symmetric pointlist: rock outlines are NOT
    # origin-symmetric, so their point AABB centre can be off by a few
    # pixels and a random shape would make this test flaky.
    rock = Rock(game.stage, Vector2d(50, 50), Rock.largeRockType)
    rock.pointlist = [(-5, -5), (5, -5), (5, 5), (-5, 5)]
    game.stage.addSprite(rock)
    assert rock.boundingRect.width > 0
    assert rock.boundingRect.height > 0
    # angle 0 -> identity rotation, integer points -> exact centre
    assert rock.boundingRect.centerx == 50
    assert rock.boundingRect.centery == 50
    assert rock.boundingRect.width == 10
    assert rock.boundingRect.height == 10


def test_check_polygon_collision_refreshes_stale_transforms(game):
    # M-3: a stale transformedPointlist (sprite moved after the last
    # draw) must not make an overlapping pair miss the collision.
    scale = Rock.scales[Rock.mediumRockType]
    rockA = Rock(game.stage, Vector2d(100, 100), Rock.mediumRockType)
    rockB = Rock(game.stage, Vector2d(100, 100), Rock.mediumRockType)
    # Identical outlines so overlap at the same position is guaranteed.
    _set_shape(rockA, 1, scale)
    _set_shape(rockB, 1, scale)

    # Draw far apart, then move them on top of each other WITHOUT
    # drawing — the old pointlists are 500 px apart.
    rockA.position.x = 1000
    rockA.position.y = 1000
    rockB.position.x = 1500
    rockB.position.y = 1000
    rockA.draw()
    rockB.draw()

    rockA.position.x = 100
    rockA.position.y = 100
    rockB.position.x = 100
    rockB.position.y = 100

    # Fresh transforms make the identical polygons intersect.
    assert rockA.checkPolygonCollision(rockB) is not None

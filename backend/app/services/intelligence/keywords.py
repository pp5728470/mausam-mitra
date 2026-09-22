from app.services.intelligence.schemas import SystemCategory

# Dictionary of category to a list of keyword tuples (phrase, weight)
CATEGORY_KEYWORDS = {
    SystemCategory.HEAVY_RAINFALL: [
        ("heavy rain", 0.9),
        ("heavy rainfall", 0.9),
        ("pouring", 0.7),
        ("downpour", 0.8),
        ("continuous rain", 0.8),
        ("raining heavily", 0.8),
    ],
    SystemCategory.FLOOD_WATERLOGGING: [
        ("flood", 0.9),
        ("flooded", 0.9),
        ("waterlogging", 0.9),
        ("waterlogged", 0.9),
        ("knee deep water", 0.8),
        ("water accumulation", 0.8),
        ("submerged", 0.9),
        ("water on road", 0.7),
    ],
    SystemCategory.STORM_STRONG_WINDS: [
        ("storm", 0.9),
        ("strong wind", 0.9),
        ("high wind", 0.8),
        ("tree fell", 0.8),
        ("trees falling", 0.8),
        ("uprooted", 0.8),
        ("gusts", 0.7),
        ("cyclone", 0.9),
    ],
    SystemCategory.LIGHTNING: [
        ("lightning", 0.9),
        ("thunderstorm", 0.8),
        ("thunder", 0.7),
        ("struck by lightning", 0.9),
    ],
    SystemCategory.EXTREME_HEAT: [
        ("heatwave", 0.9),
        ("extreme heat", 0.9),
        ("very hot", 0.7),
        ("scorching", 0.8),
        ("heat stroke", 0.9),
        ("high temperature", 0.7),
    ],
    SystemCategory.HAILSTORM: [
        ("hail", 0.9),
        ("hailstorm", 0.9),
        ("ice falling", 0.8),
        ("hailstones", 0.9),
    ],
    SystemCategory.LANDSLIDE: [
        ("landslide", 0.9),
        ("mudslide", 0.9),
        ("hill collapsed", 0.8),
        ("rocks falling", 0.7),
        ("road blocked by rocks", 0.8),
    ],
    SystemCategory.DENSE_FOG: [
        ("fog", 0.9),
        ("dense fog", 0.9),
        ("smog", 0.8),
        ("low visibility", 0.8),
        ("zero visibility", 0.9),
        ("can't see", 0.6),
    ]
}

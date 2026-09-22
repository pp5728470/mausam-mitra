from geoalchemy2.elements import WKTElement


def point_wkt(longitude: float, latitude: float) -> WKTElement:
    """Build a WKT POINT for PostGIS Geometry(Point, 4326). Note: lon, lat order."""
    return WKTElement(f"POINT({longitude} {latitude})", srid=4326)

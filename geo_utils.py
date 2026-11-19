"""Projected distance helpers for GeoPulse's Guwahati study area.

Guwahati lies in UTM zone 46N (WGS 84 / EPSG:32646). Input coordinates
are always latitude/longitude in WGS84; output distances are metres.
"""
from __future__ import annotations

import numpy as np
from pyproj import Transformer

WGS84 = "EPSG:4326"
GUWAHATI_UTM = "EPSG:32646"
_TO_UTM = Transformer.from_crs(WGS84, GUWAHATI_UTM, always_xy=True)


def project_lonlat(longitude, latitude):
    """Project longitude/latitude arrays or scalars into Guwahati UTM metres."""
    lon = np.atleast_1d(np.asarray(longitude, dtype=float))
    lat = np.atleast_1d(np.asarray(latitude, dtype=float))
    x, y = _TO_UTM.transform(lon, lat)
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)


def distance_from_site_m(site_lat: float, site_lon: float, latitudes, longitudes) -> np.ndarray:
    """Return planar UTM distance in metres from one site to many WGS84 points."""
    sx, sy = project_lonlat(float(site_lon), float(site_lat))
    px, py = project_lonlat(np.asarray(longitudes, dtype=float), np.asarray(latitudes, dtype=float))
    return np.hypot(px - sx, py - sy)


def within_radius(site_lat: float, site_lon: float, latitudes, longitudes, radius_m: float) -> np.ndarray:
    """Boolean mask for points inside a metric radius around a site."""
    if radius_m < 0:
        raise ValueError("radius_m must be non-negative")
    return distance_from_site_m(site_lat, site_lon, latitudes, longitudes) <= float(radius_m)

import numpy as np
import pytest
from geo_utils import GUWAHATI_UTM, distance_from_site_m, project_lonlat, within_radius


def test_guwahati_uses_utm_zone_46n():
    assert GUWAHATI_UTM == "EPSG:32646"
    x, y = project_lonlat(91.7362, 26.1445)
    assert np.isfinite(x) and np.isfinite(y)
    assert 300_000 < x < 800_000
    assert 2_800_000 < y < 3_200_000


def test_same_point_has_zero_distance():
    d = distance_from_site_m(26.1445, 91.7362, [26.1445], [91.7362])
    assert d[0] == pytest.approx(0, abs=0.01)


def test_500m_catchment_boundary():
    # Roughly 0.001 degrees latitude is about 111 metres at this latitude.
    mask = within_radius(26.1445, 91.7362, [26.1445, 26.1500], [91.7362, 91.7362], 500)
    assert mask.tolist() == [True, False]


def test_negative_radius_rejected():
    with pytest.raises(ValueError):
        within_radius(26.1445, 91.7362, [26.1445], [91.7362], -1)

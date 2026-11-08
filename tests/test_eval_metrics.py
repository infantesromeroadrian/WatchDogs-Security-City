"""Unit tests for the evaluation metric functions."""

import pytest

from eval import metrics as m


def test_haversine_known_distance():
    # Madrid -> Paris is about 1053 km
    assert m.haversine_km(40.4168, -3.7038, 48.8566, 2.3522) == pytest.approx(1053, abs=5)
    assert m.haversine_km(10, 10, 10, 10) == 0


def test_geolocation_summary_counts_missing_as_miss():
    s = m.geolocation_summary([1.0, 30.0, 500.0, None])
    assert s["n"] == 4 and s["n_with_prediction"] == 3
    assert s["within_25km_pct"] == 25.0
    assert s["within_200km_pct"] == 50.0
    assert s["median_error_km"] == 30.0


def test_levenshtein_and_cer():
    assert m.levenshtein("kitten", "sitting") == 3
    assert m.cer("AB 12", "ab-12") == 0.0
    assert m.cer("ABCD", "ABXD") == 0.25
    assert m.cer("", "x") == 1.0


def test_count_summary():
    s = m.count_summary([2, 4, 6], [2, 5, None])
    assert s["mae"] == round((0 + 1 + 6) / 3, 2)
    assert s["n_missing"] == 1
    assert s["exact_match_pct"] == pytest.approx(33.3, abs=0.1)


def test_sidc_scores():
    truth = "10031000001211000000"
    s = m.sidc_scores([truth, truth, truth], [truth, "10061000001211000000", "SFGPUCII--"])
    assert s["exact_16_acc_pct"] == pytest.approx(33.3, abs=0.1)
    assert s["entity_acc_pct"] == pytest.approx(66.7, abs=0.1)
    assert s["affiliation_acc_pct"] == pytest.approx(33.3, abs=0.1)
    assert s["well_formed_sidc_pct"] == pytest.approx(66.7, abs=0.1)


def test_binary_scores():
    s = m.binary_scores([True, True, False, False], [True, False, True, False])
    assert (s["tp"], s["fn"], s["fp"], s["tn"]) == (1, 1, 1, 1)
    assert s["accuracy_pct"] == 50.0

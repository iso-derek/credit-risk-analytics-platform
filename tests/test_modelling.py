import pandas as pd

from src.modelling import score_band


def test_score_band_boundaries() -> None:
    assert score_band(0.01).startswith("A")
    assert score_band(0.08).startswith("B")
    assert score_band(0.15).startswith("C")
    assert score_band(0.25).startswith("D")
    assert score_band(0.40).startswith("E")

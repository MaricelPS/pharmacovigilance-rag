"""Unit tests for disproportionality metrics using textbook examples."""
import pytest
from src.analytics.disproportionality import compute_metrics


def test_prr_van_puijenbroek_example():
    """Reproduce the ROR example from van Puijenbroek et al. 2002.

    Fictional 2x2 for cisapride and torsades de pointes:
        a=25, b=1000, c=50, d=100000
    Expected PRR ~ 48, ROR ~ 50.
    """
    m = compute_metrics(a=25, b=1000, c=50, d=100000)
    assert 45 < m.prr < 55
    assert 45 < m.ror < 55
    assert m.is_signal_ema is True
    assert m.is_signal_bcpnn is True


def test_no_signal_when_below_threshold():
    """A drug-event pair with PRR ~ 1 should not be flagged as a signal."""
    m = compute_metrics(a=10, b=990, c=100, d=9900)
    assert m.prr == pytest.approx(1.0, abs=0.1)
    assert m.is_signal_ema is False


def test_low_count_not_signal():
    """Fewer than 3 co-occurring cases should not trigger EMA signal."""
    m = compute_metrics(a=2, b=100, c=5, d=100000)
    assert m.is_signal_ema is False
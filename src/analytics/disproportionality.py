"""Disproportionality metrics for pharmacovigilance signal detection.

Given a 2x2 contingency table for a drug-event pair against all other FAERS
reports, we compute:
    - PRR (Proportional Reporting Ratio): EMA-style signal metric
    - ROR (Reporting Odds Ratio): odds-ratio analogue with 95% CI
    - IC (Information Component): Bayesian metric used by WHO/UMC

Contingency table:
                     Event X    Other events
    Drug A              a             b
    Other drugs         c             d

References:
    - EMA guideline on signal detection (EudraVigilance)
    - Bate A. et al., BCPNN, Eur J Clin Pharmacol 1998
    - van Puijenbroek EP. et al., ROR, Pharmacoepidemiol Drug Saf 2002
"""
from dataclasses import dataclass
import math


@dataclass
class SignalMetrics:
    """Full set of disproportionality metrics for a drug-event pair."""
    a: int
    b: int
    c: int
    d: int
    prr: float
    prr_chi2: float
    ror: float
    ror_ci_low: float
    ror_ci_high: float
    ic: float
    ic_ci_low: float
    is_signal_ema: bool          # PRR >= 2, chi2 >= 4, a >= 3
    is_signal_bcpnn: bool        # IC025 > 0


def _chi_square_yates(a: int, b: int, c: int, d: int) -> float:
    """Yates-corrected chi-square for a 2x2 table."""
    n = a + b + c + d
    if n == 0:
        return 0.0
    row1, row2 = a + b, c + d
    col1, col2 = a + c, b + d
    if row1 == 0 or row2 == 0 or col1 == 0 or col2 == 0:
        return 0.0
    numerator = n * (abs(a * d - b * c) - n / 2) ** 2
    denominator = row1 * row2 * col1 * col2
    return numerator / denominator if denominator > 0 else 0.0


def compute_metrics(a: int, b: int, c: int, d: int) -> SignalMetrics:
    """Compute the full metric set for a 2x2 contingency table.

    Uses Haldane-Anscombe continuity correction (add 0.5 to every cell)
    for ROR variance to avoid division by zero when a cell is zero.
    """
    # PRR
    denom_prr_num = a + b
    denom_prr_den = c + d
    if denom_prr_num == 0 or denom_prr_den == 0 or c == 0:
        prr = 0.0
    else:
        prr = (a / denom_prr_num) / (c / denom_prr_den)

    # PRR chi-square (Yates)
    chi2 = _chi_square_yates(a, b, c, d)

    # ROR with Haldane-Anscombe correction on the log-variance
    a_c, b_c, c_c, d_c = a + 0.5, b + 0.5, c + 0.5, d + 0.5
    ror = (a_c * d_c) / (b_c * c_c)
    log_ror = math.log(ror)
    se_log_ror = math.sqrt(1 / a_c + 1 / b_c + 1 / c_c + 1 / d_c)
    ror_low = math.exp(log_ror - 1.96 * se_log_ror)
    ror_high = math.exp(log_ror + 1.96 * se_log_ror)

    # Information Component (BCPNN, simplified form)
    n = a + b + c + d
    if n == 0:
        ic, ic_low = 0.0, 0.0
    else:
        p_drug = (a + b) / n
        p_event = (a + c) / n
        p_joint = a / n
        # Standard BCPNN with alpha=beta=1 gives:
        # IC = log2( (a + 0.5) / (expected + 0.5) )
        expected = p_drug * p_event * n
        ic = math.log2((a + 0.5) / (expected + 0.5))
        # Approximate variance for IC (Norén et al.)
        var_ic = (
                (1 / math.log(2)) ** 2
                * ((n - a + 0.5) / ((a + 0.5) * (1 + n)) +
                   (n - (a + b) + 0.5) / (((a + b) + 0.5) * (1 + n)) +
                   (n - (a + c) + 0.5) / (((a + c) + 0.5) * (1 + n)))
        )
        ic_low = ic - 1.96 * math.sqrt(max(var_ic, 0.0))

    is_signal_ema = (prr >= 2.0) and (chi2 >= 4.0) and (a >= 3)
    is_signal_bcpnn = ic_low > 0

    return SignalMetrics(
        a=a, b=b, c=c, d=d,
        prr=prr, prr_chi2=chi2,
        ror=ror, ror_ci_low=ror_low, ror_ci_high=ror_high,
        ic=ic, ic_ci_low=ic_low,
        is_signal_ema=is_signal_ema,
        is_signal_bcpnn=is_signal_bcpnn,
    )
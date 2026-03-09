"""
3-year volume forecast using real cohort realization rates.

Uses quarterly Volume/Tier rates derived from historical cohort data
(24 cohorts, 2020-2025). Applies convenience fee logic and a gradual
payment mix transition from the customer's starting CC-heavy mix toward
the Paystand target of 35% CC / 60% ACH / 5% Bank.
"""
from __future__ import annotations
from dataclasses import dataclass

import config as cfg


# Average Volume/Tier realization rates by quarters-since-close,
# derived from historical cohort data (16-23 cohorts per data point).
QUARTERLY_VT_RATES = [
    0.003125,  # Q0  - close quarter, barely onboarded
    0.019391,  # Q1  - ramping
    0.047682,  # Q2  - accelerating
    0.066667,  # Q3  - end of Year 1
    0.074850,  # Q4  - hitting stride
    0.078263,  # Q5
    0.082889,  # Q6
    0.093059,  # Q7  - end of Year 2
    0.092938,  # Q8  - steady state
    0.094467,  # Q9
    0.093071,  # Q10
    0.088769,  # Q11 - end of Year 3
]

STARTING_MIX = {"cc": 0.45, "ach": 0.50, "bank": 0.05}
TARGET_MIX = {"cc": 0.35, "ach": 0.60, "bank": 0.05}
MIX_TRANSITION_QUARTERS = 11  # full transition by end of Year 3


@dataclass
class VolumeForecastYear:
    year: int
    total: float
    cc: float
    ach: float
    bank_network: float

    @property
    def ach_txn_count(self) -> int:
        if cfg.ACH_AVG_TXN_SIZE <= 0:
            return 0
        return int(self.ach / cfg.ACH_AVG_TXN_SIZE)

    @property
    def bank_network_txn_count(self) -> int:
        if cfg.ACH_AVG_TXN_SIZE <= 0:
            return 0
        return int(self.bank_network / cfg.ACH_AVG_TXN_SIZE)


def _initial_payment_mix(
    conv_fee_today: int,
    conv_fee_with_paystand: int,
) -> dict[str, float]:
    """Compute the Q0 payment mix: starts from STARTING_MIX (45/50/5),
    then applies convenience-fee CC drop.

    Convenience fee CC drop:
      - Using CF today AND with Paystand -> 20% CC drop
      - CF only with Paystand (not today) -> 60% CC drop
      - Dropped CC splits 80% ACH / 20% bank
    """
    uses_cf_today = conv_fee_today > 0
    uses_cf_paystand = conv_fee_with_paystand > 0

    if uses_cf_paystand and uses_cf_today:
        cc_drop = 0.05
    elif uses_cf_paystand and not uses_cf_today:
        cc_drop = 0.10
    else:
        cc_drop = 0.0

    cc = STARTING_MIX["cc"] * (1 - cc_drop)
    dropped = STARTING_MIX["cc"] * cc_drop

    ach = STARTING_MIX["ach"] + dropped * 0.80
    bank = STARTING_MIX["bank"] + dropped * 0.20

    total = cc + ach + bank
    return {
        "cc": cc / total,
        "ach": ach / total,
        "bank": bank / total,
    }


def _mix_at_quarter(
    initial: dict[str, float],
    quarter: int,
) -> dict[str, float]:
    """Blend from initial payment mix toward target over MIX_TRANSITION_QUARTERS."""
    blend = min(quarter / MIX_TRANSITION_QUARTERS, 1.0)
    return {
        k: initial[k] * (1 - blend) + TARGET_MIX[k] * blend
        for k in ("cc", "ach", "bank")
    }


def forecast_volume_y1_y3(
    processing_tier_volume: float,
    expected_cc_volume: float,
    conv_fee_with_paystand: float,
    conv_fee_today: float,
) -> dict[int, VolumeForecastYear]:
    """
    Returns {1: VolumeForecastYear, 2: ..., 3: ...}.

    Uses real quarterly V/T realization rates, then splits volume via
    a payment mix that transitions from the customer's starting mix
    (CC-heavy, adjusted for convenience fees) toward 35/60/5.
    """
    initial_mix = _initial_payment_mix(
        int(conv_fee_today), int(conv_fee_with_paystand),
    )

    forecast: dict[int, VolumeForecastYear] = {}

    for year in (1, 2, 3):
        q_start = (year - 1) * 4
        q_end = year * 4

        year_cc = 0.0
        year_ach = 0.0
        year_bank = 0.0

        for q in range(q_start, q_end):
            vt_rate = QUARTERLY_VT_RATES[q] if q < len(QUARTERLY_VT_RATES) else QUARTERLY_VT_RATES[-1]
            q_volume = processing_tier_volume * vt_rate
            mix = _mix_at_quarter(initial_mix, q)

            year_cc += q_volume * mix["cc"]
            year_ach += q_volume * mix["ach"]
            year_bank += q_volume * mix["bank"]

        forecast[year] = VolumeForecastYear(
            year=year,
            total=year_cc + year_ach + year_bank,
            cc=year_cc,
            ach=year_ach,
            bank_network=year_bank,
        )

    return forecast

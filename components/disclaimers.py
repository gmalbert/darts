"""
components/disclaimers.py — Responsible gambling and legal disclaimers.

Call these functions in page sidebars and footers.
"""

import streamlit as st


def rg_banner(sidebar: bool = True) -> None:
    """Responsible gambling notice. Place in sidebar or page footer."""
    text = (
        "**21+ only.** Gambling involves risk. "
        "If you or someone you know has a gambling problem, "
        "call 1-800-GAMBLER or visit [ncpgambling.org](https://www.ncpgambling.org)."
    )
    container = st.sidebar if sidebar else st
    container.markdown(
        f'<div class="rg-banner">🎲 {text}</div>',
        unsafe_allow_html=True,
    )


def affiliate_disclosure(sidebar: bool = True) -> None:
    """Affiliate/material connection disclosure."""
    text = (
        "BullzIQ may earn a commission from DraftKings through referral links. "
        "This does not affect our model's picks. Picks are generated independently."
    )
    container = st.sidebar if sidebar else st
    container.markdown(
        f'<div class="affiliate-notice">📋 {text}</div>',
        unsafe_allow_html=True,
    )


def model_disclaimer(inline: bool = False) -> None:
    """Model accuracy disclaimer — show near picks."""
    text = (
        "⚠️ Model picks are for informational purposes only and are not guaranteed. "
        "Past performance does not predict future results. Bet responsibly."
    )
    if inline:
        st.info(text)
    else:
        st.markdown(
            f'<div class="rg-banner">{text}</div>',
            unsafe_allow_html=True,
        )


def dk_cta(odds: int, match_label: str) -> None:
    """DraftKings call-to-action button (geo-gated to US)."""
    odds_str = f"+{odds}" if odds > 0 else str(odds)
    st.link_button(
        label=f"Bet {odds_str} on DraftKings →",
        url="https://sportsbook.draftkings.com",
        type="primary",
        help="Must be 21+. Available in eligible US states. Gambling problem? Call 1-800-GAMBLER.",
    )


def sidebar_legal_footer() -> None:
    """Minimal legal note for sidebar — kept for backwards compatibility."""
    pass  # Content moved to page_footer()


def page_footer() -> None:
    """Full-width footer. Uses the shared Betting Oracle footer markup."""
    from footer import add_betting_oracle_footer

    add_betting_oracle_footer()

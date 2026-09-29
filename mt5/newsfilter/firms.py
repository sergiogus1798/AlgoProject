"""Each prop firm's news rule as the EA filter needs it: window, calendars, and what moves each symbol."""

# Symbol fragments whose news currency is not in their name: an index or a commodity reads the
# currency of its country. Matched as substrings of the upper-cased MT5 symbol ("US500.cash").
COUNTRY_OF = {
    "USD": ["XAU", "XAG", "GOLD", "SILVER", "USOIL", "UKOIL", "WTI", "XTI", "BRENT", "XBR",
            "US500", "USA500", "SPX", "SP500", "US100", "NAS100", "USTEC", "NDX",
            "US30", "DJ30", "WS30", "DJI", "US2000", "RUSSELL"],
    "EUR": ["GER40", "GER30", "DE40", "DE30", "DAX", "EU50", "EUSTX50", "STOXX50", "FRA40",
            "CAC40", "ESP35", "IBEX", "IT40", "NETH25", "AEX"],
    "GBP": ["UK100", "FTSE", "GB100"],
    "JPY": ["JP225", "JPN225", "NI225", "NIKKEI"],
    "AUD": ["AUS200", "ASX200", "AU200"],
    "CHF": ["SWI20", "SMI20", "CH20"],
}

# FTMO's restricted events, as "<MT5 country code>:<event_code>" under the tag a symbol matches.
FTMO_EVENTS = {
    "USD": ["US:fed-interest-rate-decision", "US:fomc-meeting-statement", "US:nonfarm-payrolls",
            "US:unemployment-rate", "US:average-hourly-earnings-mm", "US:average-hourly-earnings-yy",
            "US:gross-domestic-product-qq", "US:fomc-minutes", "US:consumer-price-index-yy"],
    "EUR": ["EU:ecb-interest-rate-decision", "EU:ecb-deposit-rate-decision"],
    "GBP": ["GB:boe-interest-rate-decision", "GB:boe-mpc-vote-cut", "GB:boe-mpc-vote-hike",
            "GB:boe-mpc-vote-unchanged", "GB:cpi-yy"],
    "CAD": ["CA:boc-interest-rate-decision", "CA:boc-rate-statement", "CA:cpi-mm",
            "CA:employment-change", "CA:unemployment-rate"],
    "AUD": ["AU:rba-interest-rate-decision", "AU:rba-rate-statement", "AU:employment-change",
            "AU:unemployment-rate", "AU:cpi-index-number", "AU:cpi-qq", "AU:cpi-yy", "AU:gdp-qq"],
    "NZD": ["NZ:rbnz-interest-rate-decision", "NZ:rbnz-rate-statement", "NZ:employment-change-qq",
            "NZ:unemployment-rate", "NZ:cpi-qq", "NZ:gdp-qq"],
    "CHF": ["CH:snb-interest-rate-decision"],
    "OIL": ["US:eia-crude-oil-stocks-change"],
}

# events: None = every HIGH-importance MT5 event, tagged with its currency; else the firm's list.
# rule_minutes: the firm's own window, no open and no close inside it.
# block_before/after: no new entry from this far before a release until this far after it.
# close_before: close positions and cancel pending orders from here until rule_minutes before.
FIRMS = {
    # rules/hantec.yaml news_window: funded accounts, 3 min, Forex Factory red folder. Owner,
    # 2026-09-29: close first, both calendars, currency + country of the index.
    "hantec": {"label": "Hantec", "rule_minutes": 3, "block_before": 5, "block_after": 5,
               "close_before": 5, "mt5_calendar": True, "forex_factory": True,
               "events": None, "country_of": COUNTRY_OF},
    # FTMO's own restricted list (ftmo.com/en/faq/can-i-trade-news/, owner 2026-09-29), by MT5
    # event_code — the name is in the terminal's language. MT5 rates half of it medium, so
    # importance cannot stand in for it (knowhow/eng/ftmo-news-vs-mt5-importance.md). Crude Oil
    # Inventories restrict only oil: tag OIL. JP225 and the European indices restrict nothing.
    # Timings are the owner's hand-made patch of 2026-05-17.
    "ftmo": {"label": "FTMO", "rule_minutes": 2, "block_before": 3, "block_after": 3,
             "close_before": 5, "mt5_calendar": True, "forex_factory": False,
             "events": FTMO_EVENTS,
             "country_of": {"USD": ["US100", "US500", "USA500", "US30", "US2000", "DXY", "USDX"],
                            "OIL": ["USOIL", "UKOIL"]}},
}

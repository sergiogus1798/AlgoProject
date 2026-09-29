
// ===== NEWS FILTER ($label): START - inputs =====
input string sNewsFilter = "----------- News Filter ($label) -----------";
input bool   EnableNewsFilter       = true;   // Master switch
input int    NewsRuleMinutes        = $rule_minutes;      // The firm's window: no open and no close this close to a release
input int    NewsBlockMinutesBefore = $block_before;      // No new entry from this many minutes before a release
input int    NewsBlockMinutesAfter  = $block_after;      // ... until this many minutes after it
input int    NewsCloseMinutesBefore = $close_before;      // Close positions and cancel pending orders from here until NewsRuleMinutes before
input bool   NewsCloseOpenPositions = true;   // An SL or TP hit inside the window is a close, so close first
input bool   NewsUseMT5Calendar     = $mt5_calendar;   // MetaQuotes calendar: $mt5_what
input bool   NewsUseForexFactory    = $forex_factory;   // Forex Factory red folder: allow https://nfs.faireconomy.media in Tools > Options > Expert Advisors
// ===== NEWS FILTER: END =====


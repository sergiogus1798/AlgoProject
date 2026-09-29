
// ===== NEWS FILTER ($label): START - helper functions =====
// Written by AlgoProject's mt5/newsfilter for $label: no trade may be opened or closed from
// NewsRuleMinutes before to NewsRuleMinutes after a restricted release that moves this symbol. The
// EA closes its positions and cancels its pending orders from NewsCloseMinutesBefore until
// NewsRuleMinutes before each release, and opens nothing from NewsBlockMinutesBefore before
// until NewsBlockMinutesAfter after it. Neither calendar exists in the Strategy Tester, so the
// filter does nothing there: a backtest of this EA is the backtest of the EA without it.

datetime newsEventTime[];
string   newsEventCurrency[];
string   newsEventTitle[];
datetime newsLoadedAt = 0;
bool     newsWarned = false;

string NEWS_FF_URL   = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
string NEWS_FF_FILE  = "AlgoProjectNewsFF.json";   // Common\Files: one download serves every EA
string NEWS_FF_CLOCK = "AlgoProjectNewsFFFetch";   // global variable: when any EA last downloaded

//+------------------------------------------------------------------+
//| Does a release of this currency move this symbol? The currencies  |
//| in its name, and for an index or a commodity its country's one.   |
//| A new index or commodity goes in mt5/newsfilter/firms.py.         |
//+------------------------------------------------------------------+
bool newsMovesSymbol(string currency){
   string sym = _Symbol;
   StringToUpper(sym);
   if(StringFind(sym, currency) >= 0) return true;
$country_of
   return false;
}

bool newsSymbolCovered(){
   string all[] = {"USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF", "CNY", "OIL"};
   for(int i = 0; i < ArraySize(all); i++)
      if(newsMovesSymbol(all[i])) return true;
   return false;
}

void newsAdd(datetime t, string currency, string title){
   if(!newsMovesSymbol(currency)) return;
   int n = ArraySize(newsEventTime);
   ArrayResize(newsEventTime, n + 1);
   ArrayResize(newsEventCurrency, n + 1);
   ArrayResize(newsEventTitle, n + 1);
   newsEventTime[n] = t;
   newsEventCurrency[n] = currency;
   newsEventTitle[n] = title;
}

//+------------------------------------------------------------------+
//| Is this MT5 calendar event restricted by $label? Returns the tag   |
//| a symbol is matched against (its currency, or OIL), "" if not.    |
//+------------------------------------------------------------------+
string newsTag(string country, string code, string currency, ENUM_CALENDAR_EVENT_IMPORTANCE importance){
$events
}

//+------------------------------------------------------------------+
//| MetaQuotes calendar, already in server time                       |
//+------------------------------------------------------------------+
void newsLoadMT5(){
   MqlCalendarValue values[];
   datetime now = TimeTradeServer();
   if(!CalendarValueHistory(values, now - PeriodSeconds(PERIOD_D1), now + PeriodSeconds(PERIOD_D1), NULL, NULL)) return;
   for(int i = 0; i < ArraySize(values); i++){
      MqlCalendarEvent event;
      if(!CalendarEventById(values[i].event_id, event)) continue;
      MqlCalendarCountry country;
      if(!CalendarCountryById(event.country_id, country)) continue;
      string tag = newsTag(country.code, event.event_code, country.currency, event.importance);
      if(tag != "") newsAdd(values[i].time, tag, event.name);
   }
}

//+------------------------------------------------------------------+
//| Forex Factory: this week's calendar, downloaded at most hourly by |
//| one EA of the terminal and read from Common\Files by all of them  |
//+------------------------------------------------------------------+
void newsFetchFF(){
   datetime now = TimeLocal();
   if(!GlobalVariableCheck(NEWS_FF_CLOCK)) GlobalVariableSet(NEWS_FF_CLOCK, 0);
   double last = GlobalVariableGet(NEWS_FF_CLOCK);
   if(now - (datetime)last < 3600) return;
   if(!GlobalVariableSetOnCondition(NEWS_FF_CLOCK, (double)now, last)) return;   // another EA took it
   char body[], data[];
   string headers;
   ResetLastError();
   int code = WebRequest("GET", NEWS_FF_URL, "", 10000, body, data, headers);
   if(code != 200){
      int err = GetLastError();
      Print("News filter: Forex Factory download failed (HTTP ", code, ", error ", err, "), retrying in 5 minutes; the MT5 calendar still applies");
      if(err == 4014) Alert("News filter: allow https://nfs.faireconomy.media in Tools > Options > Expert Advisors > WebRequest");
      GlobalVariableSet(NEWS_FF_CLOCK, (double)(now - 3300));
      return;
   }
   int h = FileOpen(NEWS_FF_FILE, FILE_WRITE | FILE_BIN | FILE_COMMON);
   if(h == INVALID_HANDLE) return;
   FileWriteArray(h, data);
   FileClose(h);
}

string newsJsonField(string item, string key){
   string tag = "\"" + key + "\":\"";
   int start = StringFind(item, tag);
   if(start < 0) return "";
   start += StringLen(tag);
   return StringSubstr(item, start, StringFind(item, "\"", start) - start);
}

void newsLoadFF(){
   int h = FileOpen(NEWS_FF_FILE, FILE_READ | FILE_BIN | FILE_COMMON);
   if(h == INVALID_HANDLE) return;
   char data[];
   FileReadArray(h, data);
   FileClose(h);
   string json = CharArrayToString(data, 0, WHOLE_ARRAY, CP_UTF8);
   StringReplace(json, "\": \"", "\":\"");
   // Forex Factory writes New York time with its offset; the server clock is UTC plus this.
   long serverShift = (long)(MathRound((double)(TimeTradeServer() - TimeGMT()) / 900.0) * 900);
   string items[];
   int n = StringSplit(json, '}', items);
   for(int i = 0; i < n; i++){
      if(newsJsonField(items[i], "impact") != "High") continue;
      string date = newsJsonField(items[i], "date");   // 2026-09-29T08:30:00-04:00
      if(StringLen(date) < 25) continue;
      datetime local = StringToTime(StringSubstr(date, 0, 4) + "." + StringSubstr(date, 5, 2) + "." +
                                    StringSubstr(date, 8, 2) + " " + StringSubstr(date, 11, 8));
      long offset = StringToInteger(StringSubstr(date, 20, 2)) * 3600 + StringToInteger(StringSubstr(date, 23, 2)) * 60;
      if(StringSubstr(date, 19, 1) == "-") offset = -offset;
      newsAdd((datetime)((long)local - offset + serverShift), newsJsonField(items[i], "country"), newsJsonField(items[i], "title"));
   }
}

void newsRefresh(){
   if(TimeLocal() - newsLoadedAt < 60) return;
   newsLoadedAt = TimeLocal();
   ArrayResize(newsEventTime, 0);
   ArrayResize(newsEventCurrency, 0);
   ArrayResize(newsEventTitle, 0);
   if(NewsUseMT5Calendar) newsLoadMT5();
   if(NewsUseForexFactory){
      newsFetchFF();
      newsLoadFF();
   }
}

bool newsHasExposure(){
   for(int i = PositionsTotal() - 1; i >= 0; i--)
      if(PositionGetTicket(i) > 0 && PositionGetInteger(POSITION_MAGIC) == MagicNumber) return true;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
      if(OrderGetTicket(i) > 0 && OrderGetInteger(ORDER_MAGIC) == MagicNumber) return true;
   return false;
}

//+------------------------------------------------------------------+
//| Called on every tick: closes before a release, and returns true   |
//| while no new entry may be opened                                  |
//+------------------------------------------------------------------+
bool handleNewsCompliance(){
   if(!EnableNewsFilter || MQLInfoInteger(MQL_TESTER)) return false;
   if(!newsWarned){
      newsWarned = true;
      if(!newsSymbolCovered())
         Alert("News filter: no restricted news maps to ", _Symbol, ", so it never blocks. If $label restricts it, add it to mt5/newsfilter/firms.py and regenerate this EA");
   }
   newsRefresh();
   static datetime lastClose = 0;
   datetime now = TimeTradeServer();
   int blockBefore = (int)MathMax(NewsBlockMinutesBefore, NewsCloseMinutesBefore);
   bool block = false;
   for(int i = 0; i < ArraySize(newsEventTime); i++){
      datetime t = newsEventTime[i];
      if(now >= t - blockBefore * 60 && now <= t + NewsBlockMinutesAfter * 60) block = true;
      if(NewsCloseOpenPositions && now >= t - NewsCloseMinutesBefore * 60 && now < t - NewsRuleMinutes * 60
         && now - lastClose >= 15 && newsHasExposure()){
         lastClose = now;
         Print("News filter: closing positions and pending orders before '", newsEventTitle[i], "' (", newsEventCurrency[i], ") at ", TimeToString(t));
         sqCloseAllPositions("Any", MagicNumber, 1, "");
         sqCloseAllPositions("Any", MagicNumber, -1, "");
      }
   }
   return block;
}
// ===== NEWS FILTER: END =====


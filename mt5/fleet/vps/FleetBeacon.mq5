//+------------------------------------------------------------------+
//| FleetBeacon — read-only telemetry of one terminal's account.     |
//| A service: no chart change, no trade function. Every BeatSeconds |
//| it writes Common\Files\fleet\<login>.json (temp file, then      |
//| rename), and <login>.history.json when the deal count changes;   |
//| the Linux collector pulls both (mt5/fleet/collect.py).           |
//| Schema 2 = schema 1 + service_started, tick size and value and   |
//| friday_close per position, hours[], charts[], news[] — the       |
//| field list is mt5/fleet/CONTRACT.md §1. Restart the service in   |
//| each terminal (Navigator > Services > FleetBeacon) after a new   |
//| .ex5 is copied in.                                               |
//+------------------------------------------------------------------+
#property service
#property copyright "AlgoProject"
#property version   "2.00"
#property description "Writes the account's state to Common\\Files\\fleet\\<login>.json. Sends no order."

input int BeatSeconds = 30;   // seconds between two writes

#define SCHEMA 2
#define FOLDER "fleet\\"

long   g_login   = 0;      // the login the cached deposit belongs to
double g_deposit = 0.0;    // first balance operation of the account
long   g_deposit_time = 0;
long   g_started = 0;      // server epoch the service started
long   g_deal_count = -1;  // whole-history deals the history file was written for

#define HOURS_KEPT 48
#define NEWS_EVERY 300     // seconds between two calendar reads

struct HourRec
  {
   long   start;
   double balance0;
   double equity0;
   double low;
   double high;
  };
HourRec g_hours[];         // the last HOURS_KEPT server hours, oldest first
string  g_news = "";       // news[] items, refreshed every NEWS_EVERY seconds
ulong   g_news_tick = 0;   // GetTickCount64 of the last calendar read

//+------------------------------------------------------------------+
string Esc(string s)
  {
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   StringReplace(s, "\r", " ");
   StringReplace(s, "\n", " ");
   StringReplace(s, "\t", " ");
   return s;
  }

string Str(const string key, const string value) { return "\"" + key + "\":\"" + Esc(value) + "\""; }
string Int(const string key, const long value)     { return "\"" + key + "\":" + IntegerToString(value); }
string Num(const string key, const double value, const int digits = 2)
  {
   return "\"" + key + "\":" + (MathIsValidNumber(value) ? DoubleToString(value, digits) : "null");
  }

int Digits_(const string symbol)
  {
   int d = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   return d > 0 ? d : 5;
  }

//+------------------------------------------------------------------+
//| The account's first balance operation: its starting size.        |
//| Read once per login — the whole history is selected for it.      |
//+------------------------------------------------------------------+
void ReadDeposit(const long login)
  {
   g_login = login;
   g_deal_count = -1;
   g_deposit = 0.0;
   g_deposit_time = 0;
   if(!HistorySelect(0, TimeTradeServer() + 86400))
      return;
   int n = HistoryDealsTotal();
   for(int i = 0; i < n; i++)
     {
      ulong t = HistoryDealGetTicket(i);
      if(t == 0)
         continue;
      if(HistoryDealGetInteger(t, DEAL_TYPE) == DEAL_TYPE_BALANCE)
        {
         g_deposit = HistoryDealGetDouble(t, DEAL_PROFIT);
         g_deposit_time = HistoryDealGetInteger(t, DEAL_TIME);
         return;
        }
     }
  }

//+------------------------------------------------------------------+
//| Server epoch of the end of the symbol's last trade session on the |
//| current or coming Friday; 0 when it has none that day.            |
//+------------------------------------------------------------------+
long FridayClose(const string symbol)
  {
   datetime from, to, last_to = 0;
   for(uint i = 0; SymbolInfoSessionTrade(symbol, FRIDAY, i, from, to); i++)
      last_to = to;
   if(last_to == 0)
      return 0;
   MqlDateTime dt;
   TimeToStruct(TimeTradeServer(), dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   int ahead = dt.day_of_week <= 5 ? 5 - dt.day_of_week : 6;
   return (long)StructToTime(dt) + ahead * 86400 + (long)last_to;
  }

//+------------------------------------------------------------------+
string Positions()
  {
   string out = "";
   int n = PositionsTotal();
   for(int i = 0; i < n; i++)
     {
      ulong t = PositionGetTicket(i);
      if(t == 0)
         continue;
      string sym = PositionGetString(POSITION_SYMBOL);
      int d = Digits_(sym);
      if(out != "")
         out += ",";
      out += "{" + Int("ticket", (long)t) + "," + Str("symbol", sym) + "," +
             Str("side", PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell") + "," +
             Num("volume", PositionGetDouble(POSITION_VOLUME)) + "," +
             Int("time", PositionGetInteger(POSITION_TIME)) + "," +
             Num("price_open", PositionGetDouble(POSITION_PRICE_OPEN), d) + "," +
             Num("price_current", PositionGetDouble(POSITION_PRICE_CURRENT), d) + "," +
             Num("sl", PositionGetDouble(POSITION_SL), d) + "," +
             Num("tp", PositionGetDouble(POSITION_TP), d) + "," +
             Num("profit", PositionGetDouble(POSITION_PROFIT)) + "," +
             Num("swap", PositionGetDouble(POSITION_SWAP)) + "," +
             Int("magic", PositionGetInteger(POSITION_MAGIC)) + "," +
             Str("comment", PositionGetString(POSITION_COMMENT)) + "," +
             Num("tick_size", SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_SIZE), d) + "," +
             Num("tick_value_loss", SymbolInfoDouble(sym, SYMBOL_TRADE_TICK_VALUE_LOSS), 5) + "," +
             Int("friday_close", FridayClose(sym)) + "}";
     }
   return out;
  }

//+------------------------------------------------------------------+
//| Every deal since `from` on the server clock, balance operations  |
//| included: the collector rebuilds the day's starting balance.     |
//+------------------------------------------------------------------+
string Deal(const ulong t)
  {
   string sym = HistoryDealGetString(t, DEAL_SYMBOL);
   return "{" + Int("ticket", (long)t) + "," +
          Int("position", HistoryDealGetInteger(t, DEAL_POSITION_ID)) + "," +
          Int("time", HistoryDealGetInteger(t, DEAL_TIME)) + "," +
          Int("type", HistoryDealGetInteger(t, DEAL_TYPE)) + "," +
          Int("entry", HistoryDealGetInteger(t, DEAL_ENTRY)) + "," +
          Str("symbol", sym) + "," +
          Num("volume", HistoryDealGetDouble(t, DEAL_VOLUME)) + "," +
          Num("price", HistoryDealGetDouble(t, DEAL_PRICE), Digits_(sym)) + "," +
          Num("profit", HistoryDealGetDouble(t, DEAL_PROFIT)) + "," +
          Num("swap", HistoryDealGetDouble(t, DEAL_SWAP)) + "," +
          Num("commission", HistoryDealGetDouble(t, DEAL_COMMISSION)) + "," +
          Num("fee", HistoryDealGetDouble(t, DEAL_FEE)) + "," +
          Int("magic", HistoryDealGetInteger(t, DEAL_MAGIC)) + "," +
          Str("comment", HistoryDealGetString(t, DEAL_COMMENT)) + "}";
  }

string Deals(const datetime from)
  {
   string out = "";
   if(!HistorySelect(from, TimeTradeServer() + 86400))
      return out;
   int n = HistoryDealsTotal();
   for(int i = 0; i < n; i++)
     {
      ulong t = HistoryDealGetTicket(i);
      if(t == 0)
         continue;
      if(out != "")
         out += ",";
      out += Deal(t);
     }
   return out;
  }

//+------------------------------------------------------------------+
//| Temp file, then rename: the collector never reads a half file.   |
//+------------------------------------------------------------------+
void WriteAtomic(const string name, const string json)
  {
   string temp = name + ".tmp";
   int h = FileOpen(temp, FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON, 0, CP_UTF8);
   if(h == INVALID_HANDLE)
     {
      PrintFormat("FleetBeacon: cannot open %s, error %d", temp, GetLastError());
      return;
     }
   FileWriteString(h, json);
   FileClose(h);
   if(!FileMove(temp, FILE_COMMON, name, FILE_COMMON | FILE_REWRITE))
      PrintFormat("FleetBeacon: cannot rename %s, error %d", temp, GetLastError());
  }

//+------------------------------------------------------------------+
//| Every deal since the account opened, only when their count moved. |
//+------------------------------------------------------------------+
void WriteHistory(const long login, const datetime server)
  {
   if(!HistorySelect(0, server + 86400) || HistoryDealsTotal() == g_deal_count)
      return;
   g_deal_count = HistoryDealsTotal();
   string json = "{" + Int("schema", SCHEMA) + "," + Int("login", login) + "," +
                 Int("written_gmt", (long)TimeGMT()) + "," + Int("server_time", (long)server) + "," +
                 "\"deals\":[" + Deals(0) + "]}";
   WriteAtomic(FOLDER + IntegerToString(login) + ".history.json", json);
  }

//+------------------------------------------------------------------+
//| One equity sample on every 500 ms pass: the hour's low and high.  |
//+------------------------------------------------------------------+
void SampleHour()
  {
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   long start = (long)TimeTradeServer() / 3600 * 3600;
   int n = ArraySize(g_hours);
   if(n == 0 || g_hours[n - 1].start != start)
     {
      if(n == HOURS_KEPT)
        {
         for(int i = 1; i < n; i++)
            g_hours[i - 1] = g_hours[i];
         n--;
        }
      ArrayResize(g_hours, n + 1);
      g_hours[n].start = start;
      g_hours[n].balance0 = AccountInfoDouble(ACCOUNT_BALANCE);
      g_hours[n].equity0 = equity;
      g_hours[n].low = equity;
      g_hours[n].high = equity;
      return;
     }
   g_hours[n - 1].low = MathMin(g_hours[n - 1].low, equity);
   g_hours[n - 1].high = MathMax(g_hours[n - 1].high, equity);
  }

string Hours()
  {
   string out = "";
   for(int i = 0; i < ArraySize(g_hours); i++)
     {
      if(out != "")
         out += ",";
      out += "{" + Int("start", g_hours[i].start) + "," + Num("balance0", g_hours[i].balance0) + "," +
             Num("equity0", g_hours[i].equity0) + "," + Num("low", g_hours[i].low) + "," +
             Num("high", g_hours[i].high) + "}";
     }
   return out;
  }

//+------------------------------------------------------------------+
//| Every chart that carries an EA.                                   |
//+------------------------------------------------------------------+
string Charts()
  {
   string out = "";
   for(long c = ChartFirst(); c >= 0; c = ChartNext(c))
     {
      string expert = ChartGetString(c, CHART_EXPERT_NAME);
      if(expert == "")
         continue;
      if(out != "")
         out += ",";
      out += "{" + Str("symbol", ChartSymbol(c)) + "," +
             Str("period", StringSubstr(EnumToString(ChartPeriod(c)), 7)) + "," +
             Str("expert", expert) + "}";
     }
   return out;
  }

//+------------------------------------------------------------------+
//| Calendar values from 1 h ago to 24 h ahead, moderate or high.     |
//| Calendar times are server time already.                           |
//+------------------------------------------------------------------+
string News()
  {
   string out = "";
   MqlCalendarValue values[];
   datetime now = TimeTradeServer();
   if(CalendarValueHistory(values, now - 3600, now + 86400) <= 0)
      return out;
   for(int i = 0; i < ArraySize(values); i++)
     {
      MqlCalendarEvent ev;
      MqlCalendarCountry country;
      if(!CalendarEventById(values[i].event_id, ev) || ev.importance < CALENDAR_IMPORTANCE_MODERATE)
         continue;
      if(!CalendarCountryById(ev.country_id, country))
         continue;
      if(out != "")
         out += ",";
      out += "{" + Int("time", (long)values[i].time) + "," + Int("event_id", (long)values[i].event_id) + "," +
             Str("code", ev.event_code) + "," + Str("currency", country.currency) + "," +
             Str("country", country.code) + "," + Int("importance", (long)ev.importance) + "," +
             Str("name", ev.name) + "}";
     }
   return out;
  }

//+------------------------------------------------------------------+
void Beat()
  {
   long login = AccountInfoInteger(ACCOUNT_LOGIN);
   if(login <= 0)
      return;                       // no account: the collector reads the silence
   if(login != g_login || g_deposit_time == 0)
      ReadDeposit(login);

   datetime server = TimeTradeServer();
   WriteHistory(login, server);
   if(g_news_tick == 0 || GetTickCount64() - g_news_tick >= NEWS_EVERY * 1000)
     {
      g_news = News();
      g_news_tick = GetTickCount64();
     }
   MqlDateTime dt;
   TimeToStruct(server, dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime day = StructToTime(dt);

   string json = "{" +
      Int("schema", SCHEMA) + "," +
      Int("written_gmt", (long)TimeGMT()) + "," +
      Int("server_time", (long)server) + "," +
      Int("day_start", (long)day) + "," +
      Int("period_s", BeatSeconds) + "," +
      Int("service_started", g_started) + "," +
      Int("login", login) + "," +
      Str("server", AccountInfoString(ACCOUNT_SERVER)) + "," +
      Str("company", AccountInfoString(ACCOUNT_COMPANY)) + "," +
      Str("currency", AccountInfoString(ACCOUNT_CURRENCY)) + "," +
      Int("leverage", AccountInfoInteger(ACCOUNT_LEVERAGE)) + "," +
      Num("balance", AccountInfoDouble(ACCOUNT_BALANCE)) + "," +
      Num("equity", AccountInfoDouble(ACCOUNT_EQUITY)) + "," +
      Num("floating", AccountInfoDouble(ACCOUNT_PROFIT)) + "," +
      Num("margin", AccountInfoDouble(ACCOUNT_MARGIN)) + "," +
      Num("margin_free", AccountInfoDouble(ACCOUNT_MARGIN_FREE)) + "," +
      Num("deposit", g_deposit) + "," +
      Int("deposit_time", g_deposit_time) + "," +
      Int("connected", TerminalInfoInteger(TERMINAL_CONNECTED)) + "," +
      Int("autotrading", TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)) + "," +
      Int("account_trade_allowed", AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)) + "," +
      Int("account_trade_expert", AccountInfoInteger(ACCOUNT_TRADE_EXPERT)) + "," +
      Int("build", TerminalInfoInteger(TERMINAL_BUILD)) + "," +
      Int("ping_us", TerminalInfoInteger(TERMINAL_PING_LAST)) + "," +
      "\"positions\":[" + Positions() + "]," +
      "\"deals_today\":[" + Deals(day) + "]," +
      "\"hours\":[" + Hours() + "]," +
      "\"charts\":[" + Charts() + "]," +
      "\"news\":[" + g_news + "]}";

   WriteAtomic(FOLDER + IntegerToString(login) + ".json", json);
  }

//+------------------------------------------------------------------+
void OnStart()
  {
   int period = MathMax(BeatSeconds, 5);
   g_started = (long)TimeTradeServer();
   PrintFormat("FleetBeacon %d started, every %d s", SCHEMA, period);
   while(!IsStopped())
     {
      Beat();
      for(int i = 0; i < period * 2 && !IsStopped(); i++)
        {
         if(AccountInfoInteger(ACCOUNT_LOGIN) > 0)
            SampleHour();
         Sleep(500);
        }
     }
  }
//+------------------------------------------------------------------+

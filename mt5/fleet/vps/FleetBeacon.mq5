//+------------------------------------------------------------------+
//| FleetBeacon — read-only telemetry of one terminal's account.     |
//| A service: no chart, no trade function. Every BeatSeconds it   |
//| writes Common\Files\fleet\<login>.json (temp file, then rename), |
//| which the Linux collector pulls (mt5/fleet, encargo 35 §2 A).    |
//+------------------------------------------------------------------+
#property service
#property copyright "AlgoProject"
#property version   "1.00"
#property description "Writes the account's state to Common\\Files\\fleet\\<login>.json. Sends no order."

input int BeatSeconds = 30;   // seconds between two writes

#define SCHEMA 1
#define FOLDER "fleet\\"

long   g_login   = 0;      // the login the cached deposit belongs to
double g_deposit = 0.0;    // first balance operation of the account
long   g_deposit_time = 0;

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
             Str("comment", PositionGetString(POSITION_COMMENT)) + "}";
     }
   return out;
  }

//+------------------------------------------------------------------+
//| Every deal since `from` on the server clock, balance operations  |
//| included: the collector rebuilds the day's starting balance.     |
//+------------------------------------------------------------------+
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
      string sym = HistoryDealGetString(t, DEAL_SYMBOL);
      if(out != "")
         out += ",";
      out += "{" + Int("ticket", (long)t) + "," +
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
      "\"deals_today\":[" + Deals(day) + "]}";

   string name = FOLDER + IntegerToString(login) + ".json";
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
void OnStart()
  {
   int period = MathMax(BeatSeconds, 5);
   PrintFormat("FleetBeacon %d started, every %d s", SCHEMA, period);
   while(!IsStopped())
     {
      Beat();
      for(int i = 0; i < period * 2 && !IsStopped(); i++)
         Sleep(500);
     }
  }
//+------------------------------------------------------------------+

// Counts the bars of the chart's timeframe the Strategy Tester walks, per month, and writes `YYYY-MM,count` lines to
// Common\Files\AlgoProbeMonths.csv. Run it on the strategy's timeframe with the ohlc_m1 model: a bar counts when its
// open time changes. Also writes `spread,<points>,<count>` lines: the spread of each M1 bar the tester walks, the
// history it prices every_tick and ohlc_m1 from (P26i A). 🔬 Not open_prices: there an M1 request ends the test
// («wrong timeframe request in Open Prices testing mode»). Trades nothing.
#property strict

int    counts[];
int    first_key = 0;  // year*12 + month-1 of counts[0]
int    spreads[];      // spreads[p]: M1 bars whose spread was p points
datetime last_bar = 0;     // open time of the chart's bar last counted
long     last_minute = 0;  // TimeCurrent()/60 of the M1 bar last sampled
int    key_of(datetime t)
{
   MqlDateTime d;
   TimeToStruct(t, d);
   return d.year * 12 + d.mon - 1;
}

void OnTick()
{
   long minute = (long)TimeCurrent() / 60;
   if(minute != last_minute)
   {
      last_minute = minute;
      int p = (int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
      if(p >= 0)
      {
         if(p >= ArraySize(spreads))
         {
            int old = ArraySize(spreads);
            ArrayResize(spreads, p + 1);
            ArrayFill(spreads, old, p + 1 - old, 0);
         }
         spreads[p]++;
      }
   }
   datetime t = iTime(_Symbol, _Period, 0);
   if(t == last_bar)
      return;
   last_bar = t;
   int k = key_of(t);
   if(ArraySize(counts) == 0)
      first_key = k;
   int i = k - first_key;
   if(i < 0)
      return;
   if(i >= ArraySize(counts))
   {
      int old = ArraySize(counts);
      ArrayResize(counts, i + 1);
      ArrayFill(counts, old, i + 1 - old, 0);
   }
   counts[i]++;
}

void OnDeinit(const int reason)
{
   int h = FileOpen("AlgoProbeMonths.csv", FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_COMMON);
   if(h == INVALID_HANDLE)
      return;
   for(int i = 0; i < ArraySize(counts); i++)
   {
      int k = first_key + i;
      FileWriteString(h, StringFormat("%04d-%02d,%d\n", k / 12, k % 12 + 1, counts[i]));
   }
   for(int p = 0; p < ArraySize(spreads); p++)
      if(spreads[p] > 0)
         FileWriteString(h, StringFormat("spread,%d,%d\n", p, spreads[p]));
   FileClose(h);
}

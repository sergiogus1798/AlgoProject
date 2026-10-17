// Counts the bars of the chart's timeframe the Strategy Tester walks, per month, and writes `YYYY-MM,count` lines to
// Common\Files\AlgoProbeMonths.csv. Run it on the strategy's timeframe with the open_prices model: the tester then
// fires one tick per bar, so the tick count is the bar count. Trades nothing.
#property strict

int    counts[];
int    first_key = 0;  // year*12 + month-1 of counts[0]
int    key_of(datetime t)
{
   MqlDateTime d;
   TimeToStruct(t, d);
   return d.year * 12 + d.mon - 1;
}

void OnTick()
{
   int k = key_of(iTime(_Symbol, _Period, 0));
   if(ArraySize(counts) == 0)
      first_key = k;
   int i = k - first_key;
   if(i < 0)
      return;
   if(i >= ArraySize(counts))
   {
      int old = ArraySize(counts);
      ArrayResize(counts, i + 1);
      for(int j = old; j <= i; j++)
         counts[j] = 0;
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
   FileClose(h);
}

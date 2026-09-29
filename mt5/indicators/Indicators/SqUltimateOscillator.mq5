//+------------------------------------------------------------------+
//|                                          SqUltimateOscillator.mq5|
//|                           Copyright © 2025, StrategyQuant s.r.o. |
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2025, StrategyQuant s.r.o."
#property link      "http://www.strategyquant.com"
#property description "Ultimate Oscillator"
#property version   "1.00"

#property indicator_separate_window
#property indicator_minimum 0
#property indicator_maximum 100
#property indicator_buffers 3
#property indicator_plots   1
#property indicator_type1   DRAW_LINE
#property indicator_color1  Green
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1
#property indicator_label1  "UO"

//---- input parameters
input int FastLength=7;
input int MiddleLength=14;
input int SlowLength=28;

//---- buffers
double UOBuffer[];        // Main indicator buffer
double BuyingPressure[];  // Buying pressure calculation buffer
double TrueRange[];       // True range calculation buffer

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   // Set up buffers
   SetIndexBuffer(0, UOBuffer, INDICATOR_DATA);
   SetIndexBuffer(1, BuyingPressure, INDICATOR_CALCULATIONS);
   SetIndexBuffer(2, TrueRange, INDICATOR_CALCULATIONS);
   
   // Set arrays as series to match MQL4 behavior
   ArraySetAsSeries(UOBuffer, true);
   ArraySetAsSeries(BuyingPressure, true);
   ArraySetAsSeries(TrueRange, true);
   
   // Set indicator name
   string short_name="UO("+IntegerToString(FastLength)+","+IntegerToString(MiddleLength)+","+IntegerToString(SlowLength)+")";
   IndicatorSetString(INDICATOR_SHORTNAME, short_name);
   
   // Set precision
   IndicatorSetInteger(INDICATOR_DIGITS, 2);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   // Make sure we have enough bars to calculate
   if(rates_total <= SlowLength)
      return(0);
   
   // Set price arrays as series to match MQL4 behavior
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   
   // Calculate starting point - match MQL4 IndicatorCounted() behavior
   int counted_bars = prev_calculated;
   if(counted_bars < 0) return(-1);
   if(counted_bars > 0) counted_bars--;
   
   int limit = rates_total - counted_bars;
   if(limit > rates_total) limit = rates_total;
   
   // Define weights for the three periods
   int Weight1 = 4;
   int Weight2 = 2;
   int Weight3 = 1;
   int TotalWeight = Weight1 + Weight2 + Weight3;
   
   // Calculate indicator values (from newest to oldest bar - exactly as in MQL4)
   for(int i = limit-1; i >= 0 && !IsStopped(); i--)
   {
      double high_val = high[i];
      double low_val = low[i];
      double close_val = close[i];
      
      if(i == rates_total-1) // First historical bar (oldest)
      {
         BuyingPressure[i] = 0;
         TrueRange[i] = high_val - low_val;
         UOBuffer[i] = 50; // Default starting value
         continue;
      }
      
      double prev_close = close[i+1];
      
      // Calculate True Low (TL) - minimum of current low or previous close
      double true_low = MathMin(low_val, prev_close);
      
      // Calculate Buying Pressure (BP) - Close - TL
      BuyingPressure[i] = close_val - true_low;
      
      // Calculate True Range (TR) - maximum of (high-low), (high-prev_close), (prev_close-low)
      TrueRange[i] = MathMax(high_val - low_val, 
                     MathMax(MathAbs(high_val - prev_close), 
                            MathAbs(prev_close - low_val)));
      
      // Need enough bars for largest period
      if(i > rates_total - SlowLength - 1)
      {
         UOBuffer[i] = 50;
         continue;
      }
      
      // Calculate Average Buying Pressure for each period
      double avg_bp1 = 0, avg_bp2 = 0, avg_bp3 = 0;
      double avg_tr1 = 0, avg_tr2 = 0, avg_tr3 = 0;
      
      // Period 1 calculations - exactly like MQL4
      for(int j = 0; j < FastLength; j++)
      {
         avg_bp1 += BuyingPressure[i+j];
         avg_tr1 += TrueRange[i+j];
      }
      
      // Period 2 calculations - exactly like MQL4
      for(int j = 0; j < MiddleLength; j++)
      {
         avg_bp2 += BuyingPressure[i+j];
         avg_tr2 += TrueRange[i+j];
      }
      
      // Period 3 calculations - exactly like MQL4
      for(int j = 0; j < SlowLength; j++)
      {
         avg_bp3 += BuyingPressure[i+j];
         avg_tr3 += TrueRange[i+j];
      }
      
      // Calculate Raw Values
      double raw1 = avg_tr1 == 0 ? 0 : (avg_bp1 / avg_tr1);
      double raw2 = avg_tr2 == 0 ? 0 : (avg_bp2 / avg_tr2);
      double raw3 = avg_tr3 == 0 ? 0 : (avg_bp3 / avg_tr3);
      
      // Calculate Ultimate Oscillator
      double uo = ((raw1 * Weight1) + (raw2 * Weight2) + (raw3 * Weight3)) * 100 / TotalWeight;
      
      UOBuffer[i] = uo;
   }
   
   return(rates_total);
}
//+------------------------------------------------------------------+
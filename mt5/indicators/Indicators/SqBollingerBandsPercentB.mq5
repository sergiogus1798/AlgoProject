//+------------------------------------------------------------------+
//|                                    SqBollingerBandsPercentB.mq5  |
//|                          Copyright © 2022, StrategyQuant s.r.o.  |
//|                                    http://www.strategyquant.com  |
//+------------------------------------------------------------------+
#property copyright   "Copyright © 2022, StrategyQuant s.r.o."
#property link        "http://www.strategyquant.com"
#property description "Bollinger Bands %B"
#property version     "1.00"

#property indicator_separate_window
#property indicator_buffers 1
#property indicator_plots   1
#property indicator_type1   DRAW_LINE
#property indicator_color1  DodgerBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1
#property indicator_label1  "PercentB"
#property indicator_minimum 0
#property indicator_maximum 1

//--- input parameters
ENUM_APPLIED_PRICE InpPrice=PRICE_CLOSE;
input int    InpPeriod=20;       // Period
input double InpDeviation=2;     // Deviation
 // Price type

//--- indicator buffers
double ExtPercentBBuffer[];   // Main visible buffer

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
//--- check for input parameters
   if(InpPeriod <= 0)
   {
      Print("Incorrect value for input variable Period=", InpPeriod, ". Indicator will use value=20 for calculations.");
      return(INIT_FAILED);
   }
   
//--- indicator buffers mapping
   SetIndexBuffer(0, ExtPercentBBuffer, INDICATOR_DATA);
   
//--- set accuracy
   IndicatorSetInteger(INDICATOR_DIGITS, 2);
   
//--- name for DataWindow and indicator subwindow label
   string short_name = "BBPercB(" + string(InpPeriod) + "," + DoubleToString(InpDeviation, 1) + ")";
   IndicatorSetString(INDICATOR_SHORTNAME, short_name);
   PlotIndexSetString(0, PLOT_LABEL, short_name);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Bollinger Bands %B                                               |
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
   // Set arrays in the same chronological order as original MQL4 code
   ArraySetAsSeries(time, false);
   ArraySetAsSeries(open, false);
   ArraySetAsSeries(high, false);
   ArraySetAsSeries(low, false);
   ArraySetAsSeries(close, false);
   ArraySetAsSeries(ExtPercentBBuffer, false);
   
   // Not enough bars to calculate
   if(rates_total < 1)
      return(0);
   
   // Determine calculation starting point
   int first;
   if(prev_calculated == 0)
      first = 0;
   else
      first = prev_calculated - 1;
   
   // The main loop of calculations - exactly following the original algorithm
   for(int i = first; i < rates_total && !IsStopped(); i++)
   {
      if(i < InpPeriod)
      {
         ExtPercentBBuffer[i] = 0.0;
         continue;
      }
      
      // Get price data based on selected price type
      double price_data[]; 
      ArrayResize(price_data, InpPeriod);
      
      for(int j = 0; j < InpPeriod; j++)
      {
         switch(InpPrice)
         {
            case PRICE_OPEN:
               price_data[j] = open[i-j];
               break;
            case PRICE_HIGH:
               price_data[j] = high[i-j];
               break;
            case PRICE_LOW:
               price_data[j] = low[i-j];
               break;
            case PRICE_MEDIAN:
               price_data[j] = (high[i-j] + low[i-j]) / 2.0;
               break;
            case PRICE_TYPICAL:
               price_data[j] = (high[i-j] + low[i-j] + close[i-j]) / 3.0;
               break;
            case PRICE_WEIGHTED:
               price_data[j] = (high[i-j] + low[i-j] + close[i-j] + close[i-j]) / 4.0;
               break;
            case PRICE_CLOSE:
            default:
               price_data[j] = close[i-j];
               break;
         }
      }
      
      // Calculate SMA
      double sum = 0.0;
      for(int j = 0; j < InpPeriod; j++)
         sum += price_data[j];
      double smaValue = sum / InpPeriod;
      
      // Calculate standard deviation
      double sumSquares = 0.0;
      for(int j = 0; j < InpPeriod; j++)
         sumSquares += MathPow(price_data[j] - smaValue, 2);
      double stdDevValue = MathSqrt(sumSquares / InpPeriod);
      
      // Calculate Bollinger Bands
      double upperBand = smaValue + InpDeviation * stdDevValue;
      double lowerBand = smaValue - InpDeviation * stdDevValue;
      double bandWidth = upperBand - lowerBand;
      
      // Get current price
      double currentPrice;
      switch(InpPrice)
      {
         case PRICE_OPEN:
            currentPrice = open[i];
            break;
         case PRICE_HIGH:
            currentPrice = high[i];
            break;
         case PRICE_LOW:
            currentPrice = low[i];
            break;
         case PRICE_MEDIAN:
            currentPrice = (high[i] + low[i]) / 2.0;
            break;
         case PRICE_TYPICAL:
            currentPrice = (high[i] + low[i] + close[i]) / 3.0;
            break;
         case PRICE_WEIGHTED:
            currentPrice = (high[i] + low[i] + close[i] + close[i]) / 4.0;
            break;
         case PRICE_CLOSE:
         default:
            currentPrice = close[i];
            break;
      }
      
      // Calculate %B
      double percentB;
      if(bandWidth == 0)
         percentB = 0.5; // Default to middle when bands are exactly the same
      else
         percentB = (currentPrice - lowerBand) / bandWidth;
      
      ExtPercentBBuffer[i] = percentB;
   }
   
   // Return value is used for next calculations
   return(rates_total);
}
//+------------------------------------------------------------------+
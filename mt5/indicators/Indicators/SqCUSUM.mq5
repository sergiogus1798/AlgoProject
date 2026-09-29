//+------------------------------------------------------------------+
//|                                                      SqCUSUM.mq5 |
//|                    © 2025,Ivan Hudec@Clonex StrategyQuant s.r.o. |
//|                                     http://www.strategyquant.com |
//|                                           hudec@strategyquant.com|
//+------------------------------------------------------------------+
#property description "Cumulative Sum (CUSUM) Indicator"
#property copyright "Copyright © 2025"
//--- indicator settings
#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots   2

#property indicator_type1   DRAW_LINE
#property indicator_color1  clrGreen
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1
#property indicator_label1  "CUSUM Positive"

#property indicator_type2   DRAW_LINE
#property indicator_color2  clrRed
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1
#property indicator_label2  "CUSUM Negative"

//--- input parameters
input int    InpPeriod=20;     // Period (1-10000)
input double InpThreshold=2.0;  // Threshold (0.1-100)
input double InpDrift=0.5;      // Drift (0-10)
input ENUM_APPLIED_PRICE InpPrice=PRICE_CLOSE;  // Applied Price

//--- indicator buffers
double ExtCusumPosBuffer[];
double ExtCusumNegBuffer[];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                           |
//+------------------------------------------------------------------+
void OnInit()
{
//--- indicator buffers mapping
   SetIndexBuffer(0,ExtCusumPosBuffer,INDICATOR_DATA);
   SetIndexBuffer(1,ExtCusumNegBuffer,INDICATOR_DATA);
   
//--- set accuracy
   IndicatorSetInteger(INDICATOR_DIGITS,_Digits+1);
   
//--- sets first bar from what index will be drawn
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,InpPeriod-1);
   PlotIndexSetInteger(1,PLOT_DRAW_BEGIN,InpPeriod-1);
   
//--- name for DataWindow and indicator subwindow label
   IndicatorSetString(INDICATOR_SHORTNAME,"CUSUM("+string(InpPeriod)+","+
                     string(InpThreshold)+","+string(InpDrift)+")");
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                                |
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
   if(rates_total < InpPeriod)
      return(0);
      
   int limit;
   if(prev_calculated < InpPeriod)
      limit = InpPeriod;
   else
      limit = prev_calculated - 1;
      
   for(int i=limit; i<rates_total && !IsStopped(); i++)
   {
      // Calculate rolling mean and standard deviation
      double sum = 0;
      double sumSquares = 0;
      
      for(int j=0; j<InpPeriod; j++)
      {
         double price = GetPrice(close, open, high, low, InpPrice, i-j);
         sum += price;
         sumSquares += price * price;
      }
      
      double mean = sum / InpPeriod;
      double variance = (sumSquares - (sum * sum / InpPeriod)) / (InpPeriod - 1);
      double stdDev = MathSqrt(variance);
      
      // Handle edge case where standard deviation is zero
      if(stdDev == 0)
         stdDev = 1;
         
      // Get current standardized value
      double currentValue = (GetPrice(close, open, high, low, InpPrice, i) - mean) / stdDev;
      
      // Calculate CUSUM values
      double prevCusumPos = (i > InpPeriod) ? ExtCusumPosBuffer[i-1] : 0;
      double prevCusumNeg = (i > InpPeriod) ? ExtCusumNegBuffer[i-1] : 0;
      
      // Upper CUSUM
      ExtCusumPosBuffer[i] = MathMax(0, prevCusumPos + currentValue - InpDrift - InpThreshold);
      
      // Lower CUSUM
      ExtCusumNegBuffer[i] = MathMax(0, prevCusumNeg - currentValue - InpDrift - InpThreshold);
   }
   
   return(rates_total);
}

//+------------------------------------------------------------------+
//| Get price based on applied price type                              |
//+------------------------------------------------------------------+
double GetPrice(const double &close[], const double &open[], 
                const double &high[], const double &low[],
                ENUM_APPLIED_PRICE price_type, int index)
{
   switch(price_type)
   {
      case PRICE_CLOSE:     return close[index];
      case PRICE_OPEN:      return open[index];
      case PRICE_HIGH:      return high[index];
      case PRICE_LOW:       return low[index];
      case PRICE_MEDIAN:    return (high[index] + low[index]) / 2.0;
      case PRICE_TYPICAL:   return (high[index] + low[index] + close[index]) / 3.0;
      case PRICE_WEIGHTED:  return (high[index] + low[index] + close[index] + close[index]) / 4.0;
      default:             return close[index];
   }
}
//+------------------------------------------------------------------+
//|                                                  SQATRPercent.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 1
#property indicator_plots 1

#property indicator_label1  "ATR Percent"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

//---- indicator parameters
input int    ATRPeriod=12;
//---- internal periods
int inATRPeriod;
//---- buffers
double ind_buffer[];
//---- handle
int atrHandle;

void OnInit()
  {
   if(ATRPeriod <= 1 ){
      printf("Incorrect value for input variable ATRPeriod=%d. Indicator will use value=%d for calculations.", ATRPeriod, 12);
      inATRPeriod = 12;
   }
   else inATRPeriod = ATRPeriod;
 
      
   ArraySetAsSeries(ind_buffer, true);
   SetIndexBuffer(0, ind_buffer,INDICATOR_DATA);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,inATRPeriod);
   
   atrHandle = iATR(NULL,0,inATRPeriod);

   
//--- indicator short name
   string short_name="SqATRPercent("+string(inATRPeriod)+")";
   IndicatorSetString(INDICATOR_SHORTNAME,short_name);
//---- end of initialization function
}
  
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
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   
   if(rates_total < inATRPeriod) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         ind_buffer[a] = 0.0;
      }
      
      limit = rates_total - inATRPeriod;
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
      double atrPerc = (roundValue(getIndicatorValue(atrHandle, 0, i))/close[i])*100;
      
      ind_buffer[i] = atrPerc;
   }
   return(rates_total);
  }
//+------------------------------------------------------------------+



double getIndicatorValue(int indyHandle, int bufferIndex, int shift){
   double buffer[];
   
   if(CopyBuffer(indyHandle, bufferIndex, shift, 1, buffer) < 0) { 
      //--- if the copying fails, tell the error code 
      PrintFormat("Failed to copy data from the indicator, error code %d", GetLastError()); 
      //--- quit with zero result - it means that the indicator is considered as not calculated 
      return(0); 
   } 
   
   double val = buffer[0];
   return val;
}

double roundValue(double value){
    return NormalizeDouble(value + 0.0000000001, 5);
}
//+------------------------------------------------------------------+
//|                                                         SqDPO.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots 1

#property indicator_label1  "SqDPO"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

//---- indicator parameters
input int   DPOPeriod=10;



//---- buffers
double ind_buffer[];
double sma_buffer[];
//---- handle

void OnInit()
  {
   
      
   ArraySetAsSeries(ind_buffer, true);
   ArraySetAsSeries(sma_buffer, true);
   SetIndexBuffer(0, ind_buffer,INDICATOR_DATA);
   SetIndexBuffer(1, sma_buffer,INDICATOR_CALCULATIONS);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,DPOPeriod);
   
  
//--- indicator short name
   string short_name="SqDPO("+string(DPOPeriod)+")";
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
   int n = DPOPeriod / 2 + 1;
   
   if(rates_total < DPOPeriod) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         ind_buffer[a] = 0.0;
      }
      
      limit = rates_total - (DPOPeriod+n);
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
   
      double sum =0;
      int count =0;
      int k = 0;
      for(k = i+n;k<(i+DPOPeriod+n);k++){
      
      sum = sum+close[k];
          
      }
      double avg = sum/DPOPeriod;

      ind_buffer[i] = close[i]-avg;
  
       
   }
   return(rates_total);
  }
//+------------------------------------------------------------------+

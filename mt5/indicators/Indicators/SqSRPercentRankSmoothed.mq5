//+------------------------------------------------------------------+
//|                                         SRPercentRankSmoothed.mq5|
//|                            Copyright © @2023 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"
#include <MovingAverages.mqh>


#property indicator_separate_window

#property indicator_buffers 2
#property indicator_plots 2

#property indicator_label1  "SR Percent Rank Smoothed"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red
#property indicator_type2  DRAW_LINE
#property indicator_color2 Blue

//---- indicator parameters

input int Lenght=120;
input int SmoothPer=12;
input int ATRPeriod=12;
input double Multiplication  =1;



//---- buffers
double ind_buffer[];
double smooth_buffer[];
//---- handle
int atrHandle;

void OnInit()
{
      
   ArraySetAsSeries(ind_buffer, true);
   SetIndexBuffer(0, ind_buffer,INDICATOR_DATA);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,Lenght);
   ArraySetAsSeries(smooth_buffer, true);
   SetIndexBuffer(1, smooth_buffer,INDICATOR_DATA);
   PlotIndexSetInteger(1,PLOT_DRAW_BEGIN,SmoothPer);
   
   atrHandle = iATR(NULL,0,ATRPeriod);

   
//--- indicator short name
   string short_name="SRPercentRankSmoothed("+string(Lenght)+","+string(SmoothPer)+","+string(ATRPeriod)+","+string(Multiplication)+")";
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
   
   if(rates_total < MathMax(ATRPeriod,MathMax(Lenght,SmoothPer))) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         ind_buffer[a] = 0.0;
         smooth_buffer[a] = 0.0;
      }
      
      limit = rates_total - MathMax(ATRPeriod,MathMax(Lenght,SmoothPer));
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
      
   
      double count =0;  
      for(int a = 1; a <=MathMax(ATRPeriod,MathMax(Lenght,SmoothPer)); a++)
        {
        

                
           double atrValue = getIndicatorValue(atrHandle, 0, i);
           if(close[i]> (low[i+a]-atrValue*Multiplication) && close[i]< high[i+a]+atrValue*Multiplication)
              {
               count++;
              }
        

       }
           
       double percrank = (double)count/Lenght*100;
       ind_buffer[i] = percrank;
       SimpleMAOnBuffer(rates_total,prev_calculated,i,SmoothPer,ind_buffer,smooth_buffer);
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
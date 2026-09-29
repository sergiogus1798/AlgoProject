//+------------------------------------------------------------------+
//|                                   SqHullMovingAverageATRBands.mq5|
//|                            Copyright © @2023 StrategyQuant s.r.o.|
//|                               https://strategyquant.com/?irgwc=1 |
//+------------------------------------------------------------------+
#property  copyright "Copyright © Clonex @ 2023 StrategyQuant s.r.o."
#property  link      "https://strategyquant.com/?irgwc=1"

#property indicator_chart_window
#property indicator_buffers 4
#property indicator_plots 3

#property indicator_label1  "Upper"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Blue
#property indicator_label2  "Lower"
#property indicator_type2  DRAW_LINE
#property indicator_color2 Blue
#property indicator_label3  "Middle"
#property indicator_type3  DRAW_LINE
#property indicator_color3 Red


//---- indicator parameters

input int    HullPeriod=20;
input double   Multiplication=1.0;
input ENUM_APPLIED_PRICE inpPrice   = PRICE_CLOSE;
//---- internal periods
//---- buffers
double hull_middle[];
double hull_upper[];
double hull_lower[];
double atr_buffer[];
//---- handle
int hull_handle;
int atr_handle;


void OnInit()
  {

 
      
   ArraySetAsSeries(hull_middle, true);
   ArraySetAsSeries(hull_upper, true);
   ArraySetAsSeries(hull_lower, true);
   ArraySetAsSeries(atr_buffer, true);
   SetIndexBuffer(2, hull_middle,INDICATOR_DATA);
   SetIndexBuffer(0, hull_upper,INDICATOR_DATA);
   SetIndexBuffer(1, hull_lower,INDICATOR_DATA);
   SetIndexBuffer(3, atr_buffer,INDICATOR_DATA);
   
   

   hull_handle = iCustom(NULL,0,"SqHullMovingAverage",HullPeriod,inpPrice);
   atr_handle = iATR(NULL,0,HullPeriod);


   
//--- indicator short name
   string short_name="SqHullMovingAverageATRBands("+IntegerToString(HullPeriod)/*+","+IntegerToString(ATRPeriod)+","*/+IntegerToString(Multiplication)+","+
                      IntegerToString(inpPrice)+")";
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
   
   if(rates_total < HullPeriod) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         hull_middle[a] = 0.0;
         atr_buffer[a] = 0.0;
         hull_upper[a] = 0.0;
         hull_lower[a] = 0.0;
      }
      
      limit = rates_total - HullPeriod;
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
 
      
      hull_middle[i] = getIndicatorValue(hull_handle, 0, i);
      hull_upper[i] = getIndicatorValue(hull_handle, 0, i)+Multiplication*getIndicatorValue(atr_handle, 0, i);
      hull_lower[i] = getIndicatorValue(hull_handle, 0, i)-Multiplication*getIndicatorValue(atr_handle, 0, i);

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

double GetStdDev(const double &arr[],int size)
{
    if(size<2)return(0.0);
    
    double sum = 0.0;
    for(int i=0;i<size;i++)
    {
      sum = sum + arr[i];
    }
        
      sum = sum/size;    
    
    double sum2 = 0.0;
    for(int i=0;i<size;i++)
    {
      sum2 = sum2 + (arr[i]- sum) * (arr[i]- sum);
    }  
      
      sum2 = sum2/(size-1);      
      sum2 = MathSqrt(sum2);
      
      return(sum2);
}
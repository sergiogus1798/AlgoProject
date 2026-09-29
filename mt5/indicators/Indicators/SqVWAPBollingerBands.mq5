//+------------------------------------------------------------------+
//|                                          SqVWAPBollingerBands.mq5|
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
#property indicator_color1 Red
#property indicator_width1 2
#property indicator_label2  "Lower"
#property indicator_type2  DRAW_LINE
#property indicator_color2 Red
#property indicator_width2 2
#property indicator_label3  "Middle"
#property indicator_type3  DRAW_LINE
#property indicator_color3 Blue
#property indicator_width3 2

//---- indicator parameters
input int    VWAPPeriod=24;
input double   Deviation=2.0;
//---- buffers
double VWAP_Middle[];
double VWAP_Upper[];
double VWAP_Lower[];
double stdev_buffer[];
//---- handle
int VWAP_handle;
int stdev_handle;


void OnInit()
  {
  
  

 
      
   ArraySetAsSeries(VWAP_Middle, true);
   ArraySetAsSeries(VWAP_Upper, true);
   ArraySetAsSeries(VWAP_Lower, true);
   ArraySetAsSeries(stdev_buffer, true);
   SetIndexBuffer(1,VWAP_Lower ,INDICATOR_DATA);
   SetIndexBuffer(0, VWAP_Upper,INDICATOR_DATA);
   SetIndexBuffer(2, VWAP_Middle,INDICATOR_DATA);;
   SetIndexBuffer(3, stdev_buffer,INDICATOR_DATA);
   VWAP_handle = iCustom(Symbol(),Period(),"SqVWAP",VWAPPeriod);
   stdev_handle = iStdDev(Symbol(),Period(),VWAPPeriod,0,MODE_SMA,VWAP_handle);

   int max = MathMax(VWAPPeriod,VWAPPeriod);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,max+1);
   PlotIndexSetInteger(1,PLOT_DRAW_BEGIN,max+1);
   PlotIndexSetInteger(2,PLOT_DRAW_BEGIN,max+1);
   PlotIndexSetInteger(3,PLOT_DRAW_BEGIN,max+1);
//--- indicator short name
   string short_name="SqVWAPBollingerBands("+IntegerToString(VWAPPeriod)+/*","+IntegerToString(BollPeriod)+*/","+IntegerToString(Deviation)+")";
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
   
   if(rates_total < VWAPPeriod) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         VWAP_Middle[a] = 0.0;
         stdev_buffer[a] = 0.0;
      }
      
      limit = rates_total - VWAPPeriod;
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
 
      
      VWAP_Middle[i] = getIndicatorValue(VWAP_handle, 0, i);
      VWAP_Upper[i] = getIndicatorValue(VWAP_handle, 0, i)+Deviation*getIndicatorValue(stdev_handle, 0, i);
      VWAP_Lower[i] = getIndicatorValue(VWAP_handle, 0, i)-Deviation*getIndicatorValue(stdev_handle, 0, i);

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
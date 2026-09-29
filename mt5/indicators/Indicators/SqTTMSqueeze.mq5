//+------------------------------------------------------------------+
//|                                                  SqTTMSqueeze.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots 2

#property indicator_label1  "Squeeze"
//#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

#property indicator_label2  "Squeeze Momentum"
//#property indicator_type2  DRAW_NONE
#property indicator_color2 Blue

//---- indicator parameters
input int BBPeriod=20;
input int KCPeriod=20;
input int LinRegPeriod=20;
input int MomPeriod=20;
input double BBDeviation=2;
input double NumATRs=2;

//---- buffers
double squeeze_buffer[];
double squeezeMomentum_buffer[];


//---- handle

int bbHandle;
int linRegHandle;
int kCHandle;


void OnInit()
  {

   ArraySetAsSeries(squeeze_buffer, true);  
   ArraySetAsSeries(squeezeMomentum_buffer, true);
   SetIndexBuffer(0, squeeze_buffer,INDICATOR_DATA);
   SetIndexBuffer(1, squeezeMomentum_buffer,INDICATOR_DATA);
   PlotIndexSetInteger(0,PLOT_DRAW_TYPE,DRAW_LINE);
   PlotIndexSetInteger(0,PLOT_LINE_STYLE,STYLE_DOT);
   PlotIndexSetInteger(0,PLOT_LINE_COLOR,clrBlue);
   PlotIndexSetInteger(1,PLOT_DRAW_TYPE,DRAW_LINE);
   PlotIndexSetInteger(1,PLOT_LINE_STYLE,STYLE_SOLID);
   PlotIndexSetInteger(1,PLOT_LINE_COLOR,clrRed);

   bbHandle = iBands(NULL,0,BBPeriod,0,BBDeviation,PRICE_CLOSE);
   linRegHandle = iCustom(NULL, 0, "SqLinReg", LinRegPeriod,PRICE_CLOSE);
   kCHandle = iCustom(NULL, 0, "SqKeltnerChannel", KCPeriod,NumATRs);
   

   
//--- indicator short name
   string short_name="SqTTMSqueeze("+string(BBPeriod)+","+string(KCPeriod)+","+string(LinRegPeriod)+","+string(MomPeriod)+","+string(BBDeviation)+","+string(NumATRs)+")";
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
   
   if(rates_total < BBPeriod) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         squeeze_buffer[a] = 0.0;
         squeezeMomentum_buffer[a]  = 0.0;
      }
      
      limit = rates_total - BBPeriod;
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
           
       double bbUpperHandleValue = getIndicatorValue(bbHandle,1,i);
       double bbLowerHandleValue = getIndicatorValue(bbHandle,2,i);
       double linRegHandleValue = getIndicatorValue(linRegHandle,0,i);
       double KCHandleUpperValue = getIndicatorValue(kCHandle,0,i);
       double KCHandleLowerValue = getIndicatorValue(kCHandle,1,i);
       double lrMomValue = getIndicatorValue(linRegHandle,0,i) - getIndicatorValue(linRegHandle,0,i+MomPeriod);
       
       
       if(bbUpperHandleValue<=KCHandleUpperValue&bbLowerHandleValue>=KCHandleLowerValue){
         squeeze_buffer[i]=1;

       }
       else{
         squeeze_buffer[i]=0;
       
       }
       
       squeezeMomentum_buffer[i] = lrMomValue;
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
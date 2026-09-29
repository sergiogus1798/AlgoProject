//+------------------------------------------------------------------+
//|                                                   SqBHErgodic.mq5|
//|                            Copyright © @2022 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"
#include <MovingAverages.mqh>
#property indicator_separate_window
#property indicator_buffers 10
#property indicator_plots 2


#property indicator_type1   DRAW_LINE
//---- colors
#property indicator_color1 Blue

#property indicator_type2   DRAW_LINE
//---- colors
#property indicator_color2 Red




//---- indicator parameters
input int R=2;
input int S=10;
input int U=5;
input int Trigger=3;


//---- buffers
double tsi[];
double sig[];
double avg1Buffer[];
double avg2Buffer[];
double avg3Buffer[];
double avg4Buffer[];
double avg5Buffer[];
double avg6Buffer[];
double avg7Buffer[];
double avg8Buffer[];
//---- handle

void OnInit()
  {
   
      
   //SetIndexDrawBegin(0,MathMax(U,MathMax(Trigger,MathMax(S,R))));
   //ndicatorDigits(MarketInfo(Symbol(),MODE_DIGITS)+2);
   SetIndexBuffer(0,tsi,INDICATOR_DATA);
   SetIndexBuffer(1,sig,INDICATOR_DATA);
   SetIndexBuffer(2,avg1Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(3,avg2Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(4,avg3Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(5,avg4Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(6,avg5Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(7,avg6Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(8,avg7Buffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(9,avg8Buffer,INDICATOR_CALCULATIONS);
   ArraySetAsSeries(tsi, true);
   ArraySetAsSeries(sig, true);
   ArraySetAsSeries(avg1Buffer, true);
   ArraySetAsSeries(avg2Buffer, true);
   ArraySetAsSeries(avg3Buffer, true);
   ArraySetAsSeries(avg4Buffer, true);
   ArraySetAsSeries(avg5Buffer, true);
   ArraySetAsSeries(avg6Buffer, true);
   ArraySetAsSeries(avg7Buffer, true);
   ArraySetAsSeries(avg8Buffer, true);

   string short_name="SqBHErgodic("+R+","+S+","+U+","+Trigger+")";
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
   

   
   if(rates_total < MathMax(R,MathMax(S,MathMax(U,Trigger)))) return(0);
   
   int limit;
    
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         tsi[a] = 0.0;
         sig[a] = 0.0;
         avg1Buffer[a] = 0.0;
         avg2Buffer[a] = 0.0;
         avg3Buffer[a] = 0.0;
         avg4Buffer[a] = 0.0;
         avg5Buffer[a] = 0.0;
         avg6Buffer[a] = 0.0;
         avg7Buffer[a] = 0.0;
         avg8Buffer[a] = 0.0;

      }
      
      limit = rates_total - MathMax(R,MathMax(S,MathMax(U,Trigger)));
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
     
      avg1Buffer[i] = close[i]-close[i+1];
      avg5Buffer[i] = fabs(close[i]-close[i+1]);
        
      }
      
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,R,avg1Buffer,avg2Buffer);
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,S,avg2Buffer,avg3Buffer);
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,U,avg3Buffer,avg4Buffer);
            
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,R,avg5Buffer,avg6Buffer);
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,S,avg6Buffer,avg7Buffer);
      ExponentialMAOnBuffer(rates_total,prev_calculated,1,U,avg7Buffer,avg8Buffer);
      
      
   for(int i=limit-1; i>=0; i--) {
     
     
      double avg = avg4Buffer[i];
      double ava = avg8Buffer[i];

      tsi[i] = (ava != 0) ? 100.0*avg/ava : 0;
      }
      
    ExponentialMAOnBuffer(rates_total,prev_calculated,0,Trigger,tsi,sig);


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
//+------------------------------------------------------------------+
//|                                                  SqCSSARegime.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 3
#property indicator_plots 1

#property indicator_label1  "SqCSSARegime"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

//---- indicator parameters
input int HLSumPeriod=10;
input int HLPeriod=10;
input int AvgPeriod=60;
input int PercentRankPeriod=120;



//---- buffers
double IndiBuffer[];
double avgBuffer[];
double avgLoopBuffer[];
//---- handle

void OnInit()
  {
   
      
   ArraySetAsSeries(IndiBuffer, true);
   ArraySetAsSeries(avgBuffer, true);
   ArraySetAsSeries(avgLoopBuffer, true);
   SetIndexBuffer(0, IndiBuffer,INDICATOR_DATA);
   SetIndexBuffer(1, avgBuffer,INDICATOR_CALCULATIONS);
   SetIndexBuffer(2, avgLoopBuffer,INDICATOR_CALCULATIONS);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,MathMax(AvgPeriod,MathMax(PercentRankPeriod,MathMax(HLPeriod,HLSumPeriod))));
   
  
//--- indicator short name
   string short_name="SqCSSARegime("+HLSumPeriod+","+HLPeriod+","+AvgPeriod+","+PercentRankPeriod+")";
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
   
   if(rates_total < MathMax(AvgPeriod,MathMax(PercentRankPeriod,MathMax(HLPeriod,HLSumPeriod)))) return(0);
   
   int limit;
    double TenDayRange,RawMetric,pRank;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         IndiBuffer[a] = 0.0;
         avgBuffer[a] = 0.0;
         avgLoopBuffer[a] = 0.0;
      }
      
      limit = rates_total - MathMax(AvgPeriod,MathMax(PercentRankPeriod,MathMax(HLPeriod,HLSumPeriod)));
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
      int count =0;
      double HLSum =0;

      for(int s = 0; s<= HLSumPeriod; s++){
      
      HLSum += (high[i+s]-low[i+s]);
      }
      
      double highestPrice = high[iHighest(Symbol(), 0, MODE_HIGH, HLPeriod, i)];
      double lowestPrice = low[iLowest(Symbol(), 0, MODE_LOW, HLPeriod, i)];
      
      TenDayRange = highestPrice-lowestPrice;
      if(TenDayRange !=0) RawMetric = HLSum/TenDayRange;
      
      avgBuffer[i] = RawMetric;
      double avg = 0;
      double sum = 0;
      for(int x = 0;x<AvgPeriod;x++){
      sum = sum + avgBuffer[i+x];
      }
      avg = sum/AvgPeriod;
      avgLoopBuffer[i] = avg;
      
     double Rank = 0;
     for(int p = 1;p<=PercentRankPeriod;p++){
      
      if(avg>avgLoopBuffer[i+p]) Rank++;

      }

      pRank = (double)Rank/PercentRankPeriod*100;
      

      IndiBuffer[i] =pRank;
   
   

       
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
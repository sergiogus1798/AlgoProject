//+------------------------------------------------------------------+
//|                                                         SqDVO.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 2
#property indicator_plots 1

#property indicator_label1  "SqDVO"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

//---- indicator parameters
input int    MAPeriod=2;
input int    PercentRankPeriod=120;


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
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,MathMax(MAPeriod,PercentRankPeriod ));
   
  
//--- indicator short name
   string short_name="SqDVO("+string(MAPeriod)+","+string(PercentRankPeriod)+")";
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
   
   if(rates_total < MathMax(MAPeriod,PercentRankPeriod )) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         ind_buffer[a] = 0.0;
      }
      
      limit = rates_total - MathMax(MAPeriod,PercentRankPeriod );
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
   
      int count =0;
      double sum =0;
      double dvo = 0;
      int rank = 0;
      
     
      
      for(int s = 0; s< MAPeriod; s++)
        {
        
            if((high[i+s]+low[i+s])!=0)sum = sum +(close[i+s]/((high[i+s]+low[i+s])/2));
        
       }
       sma_buffer[i] = sum/MAPeriod;
       
       int pRank =0;
       for(int p = 1; p<= PercentRankPeriod; p++){
            
            if(NormalizeDouble(sma_buffer[i],6)>NormalizeDouble(sma_buffer[i+p],6)){
               
               pRank = pRank +1;
              
         }
         
        dvo = 100*pRank/(double)PercentRankPeriod;
      
       }
       
       ind_buffer[i] = dvo;
       
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
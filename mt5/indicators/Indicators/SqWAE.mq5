//+------------------------------------------------------------------+
//|                                                         SqWAE.mq5|
//|                            Copyright © @2022 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 4
#property indicator_plots 4

//#property indicator_label1  "SqWAE"


#property  indicator_color1  Yellow
#property indicator_type1  DRAW_LINE
#property indicator_label1 "WAEPositive"
#property  indicator_color2  Red
#property indicator_type2  DRAW_LINE
#property indicator_label2 "WAENegative"
#property  indicator_color3  Blue
#property indicator_type3  DRAW_LINE
#property indicator_label3 "Explosion"
#property  indicator_color4  White
#property indicator_type4  DRAW_LINE
#property indicator_label4 "Dead"

//---- indicator parameters
input int  FEMA = 12;
input int  SEMA = 26;
input int  SignalMA = 9;
input int  ATRPeriod = 14;
input int  BBandPeriod = 20;
input double  BBandSD = 2.5;
input int  Sensetive = 90;
input double  DeadZonePip = 1.5;
ENUM_APPLIED_PRICE WaePrice = PRICE_MEDIAN;

   

//---- buffers
double   WAEPositive[];
double   WAENegative[];
double   Explosion[];
double   DeadBuff[];
//---- handle
int MACD_Handle,BB_Handle,ATR_Handle;

void OnInit()
  {
   
      
   ArraySetAsSeries(WAEPositive, true);
   ArraySetAsSeries(WAENegative, true);
   ArraySetAsSeries(Explosion, true);
   ArraySetAsSeries(DeadBuff, true);
   SetIndexBuffer(0, WAEPositive,INDICATOR_DATA);
   SetIndexBuffer(1, WAENegative,INDICATOR_DATA);
   SetIndexBuffer(2, Explosion,INDICATOR_DATA);
   SetIndexBuffer(3, DeadBuff,INDICATOR_DATA);
 
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,MathMax(FEMA,MathMax(SEMA,MathMax(SignalMA,MathMax(ATRPeriod,MathMax(BBandPeriod,Sensetive))))));

//---- getting handle of the iMACD indicator
   MACD_Handle=iMACD(NULL,0,FEMA,SEMA,SignalMA,PRICE_MEDIAN);
   if(MACD_Handle==INVALID_HANDLE)Print(" Failed to get handle of the iMACD indicator");
//---- getting handle of the iBands indicator
   BB_Handle=iBands(NULL,0,BBandPeriod,0,BBandSD,PRICE_MEDIAN);
   if(BB_Handle==INVALID_HANDLE)Print(" Failed to get handle of the iBands indicator");
  
     ATR_Handle=iATR(NULL,0,ATRPeriod);   
  
//--- indicator short name
   //string short_name="SqCSSARegime("+HLSumPeriod+","+HLPeriod+","+AvgPeriod+","+PercentRankPeriod+")";
   //IndicatorSetString(INDICATOR_SHORTNAME,short_name);
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
   
   //if(rates_total < MathMax(AvgPeriod,MathMax(PercentRankPeriod,MathMax(HLPeriod,HLSumPeriod)))) return(0);
   if(rates_total < MathMax(FEMA,MathMax(SEMA,MathMax(SignalMA,MathMax(ATRPeriod,MathMax(BBandPeriod,Sensetive)))))) return(0);
   int limit;

   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         WAEPositive[a] =0;
         WAENegative[a] =0;
         Explosion[a] =0;
         DeadBuff[a] =0;
      }
      
      limit = rates_total - MathMax(FEMA,MathMax(SEMA,MathMax(SignalMA,MathMax(ATRPeriod,MathMax(BBandPeriod,Sensetive)))));
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   
      int count =0;
      double HLSum =0;
      
      double atrValue =  getIndicatorValue(ATR_Handle, 0,i) ;
      
      double shiftMACDValue =  getIndicatorValue(MACD_Handle, 0,i) ;
      double shift1MACDValue =  getIndicatorValue(MACD_Handle, 0,i+1) ;
      double shift2MACDValue =  getIndicatorValue(MACD_Handle, 0,i+2) ;
      double shift3MACDValue =  getIndicatorValue(MACD_Handle, 0,i+3) ;
      
      
      double shiftBBValueUpper =  getIndicatorValue(BB_Handle, 1,i) ;
      double shiftBBValueLower =  getIndicatorValue(BB_Handle, 2,i) ;
      double shift1BBValueUpper =  getIndicatorValue(BB_Handle, 0,i+1) ;
      double shift1BBValueLower =  getIndicatorValue(BB_Handle, 1,i+1) ;
      
      
      double Trend1 = (shiftMACDValue-shift1MACDValue)*Sensetive;
      double Explo1 = (shiftBBValueUpper-shiftBBValueLower);
      double dead = getIndicatorValue(ATR_Handle, 0,i)*DeadZonePip ;
      
       if(Trend1 >= 0)
           WAEPositive[i] = Trend1;
       if(Trend1 < 0)
           WAENegative[i] = (-1*Trend1);
     
      Explosion[i] = Explo1;
      DeadBuff[i] = dead;
   

       
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
//+------------------------------------------------------------------+
//|                                                        SqCMMA.mq5|
//|                            Copyright © @2022 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 1
#property indicator_plots   1

#property indicator_label1  "CMMA"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDarkViolet
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1

//---- indicator parameters
input int                  lookback    = 10; 
input int                  atr_length = 100;

//---- buffers
double   output[];

//---- handle
int      handle_LogATR; 

int OnInit()
  {
        
   ArraySetAsSeries(output, true);
   SetIndexBuffer(0, output,INDICATOR_DATA);
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,MathMax(atr_length,atr_length ));
   
  
//--- indicator short name
   string short_name="SqCMMA("+string(lookback)+","+string(atr_length)+")";
   IndicatorSetString(INDICATOR_SHORTNAME,short_name);


//--- create handle of the indicator iMA
   handle_LogATR=iCustom(NULL,0,"SqLogATR",atr_length);
   
  

//--- if the handle is not created
   if(handle_LogATR==INVALID_HANDLE)
     {
      //--- tell about the failure and output the error code
      PrintFormat("Failed to create handle of the iMA indicator for the symbol %s/%s, error code %d",
                  Symbol(),
                  EnumToString(Period()),
                  GetLastError());
      //--- the indicator is stopped early
      return(INIT_FAILED);
     }
 
//---
   return(INIT_SUCCEEDED);
  }

//---- end of initialization function



  
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
   
   if(rates_total < MathMax(lookback+1,atr_length )) return(0);
   
   int limit;
   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         output[a] = 0.0;
      }
      
      limit = rates_total - MathMax(lookback+1,atr_length );
   }
 //--- main indicator loop
 
   for(int i=limit-1; i>=0; i--) {
   

      double denom = getIndicatorValue(handle_LogATR, 0, i);
      double sum = 0;
      
      
      for(int s = 0; s< lookback; s++){

        sum += log(close[i+s]);
        
       }
       
       sum /= lookback;
       
       double val = 0;
       if (denom > 0) {
             
          denom = denom * MathSqrt(lookback+1);
          val = (MathLog(close[i])-sum)/denom;
          val = 100 * normal_cdf(1.0 * val) - 50;
          
          }
         else val = 0;
		
       
       output[i] = val;
       
   }
   return(rates_total);
  
//+------------------------------------------------------------------+
}


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



double normal_cdf (double z) {
		double zz = MathAbs ( z ) ;
		double pdf = MathExp ( -0.5 * zz * zz ) / MathSqrt ( 2.0 * 3.141592653589793 ) ;
		double t = 1.0 / (1.0 + zz * 0.2316419) ;
		double poly = ((((1.330274429 * t - 1.821255978) * t + 1.781477937) * t -
							0.356563782) * t + 0.319381530) * t ;
		return (z > 0.0)  ?  1.0 - pdf * poly  :  pdf * poly ;
	}
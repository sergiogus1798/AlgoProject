//+------------------------------------------------------------------+
//|                                                 SqEntropyMath.mq5|
//|                            Copyright © @2021 StrategyQuant s.r.o.|
//|                                     http://www.strategyquant.com |
//+------------------------------------------------------------------+
#property  copyright "Copyright © @2021 StrategyQuant s.r.o."
#property  link      "http://www.strategyquant.com"

#property indicator_separate_window
#property indicator_buffers 1
#property indicator_plots 1

#property indicator_label1  "SqEntropyMath"
#property indicator_type1  DRAW_LINE
#property indicator_color1 Red

//---- indicator parameters
input int EMPeriod=10;




//---- buffers
double IndiBuffer[];

//---- handle

void OnInit()
  {
   
      
   ArraySetAsSeries(IndiBuffer, true);

   SetIndexBuffer(0, IndiBuffer,INDICATOR_DATA);

   //PlotIndexSetInteger(0,EMPeriod);
   
  
//--- indicator short name
   string short_name="SqEntropyMath("+EMPeriod+")";
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
   
   if(rates_total < EMPeriod) return(0);
   
   int limit;

   
   if(prev_calculated > 0) limit = rates_total - prev_calculated + 1;
   else {
      for(int a=0; a<rates_total; a++){
         IndiBuffer[a] = 0.0;

      }
      
      limit = rates_total - EMPeriod-1;
   }
 //--- main indicator loop
 
    double  P,G;
   int in,out;

   double sumx=0.0;
   double sumx2= 0.0;
   double avgx = 0.0;
   double rmsx = 0.0;
   
    in=0;  //price;
   out=0; //entropy;
 
   for(int i=limit-1; i>=0; i--) {
   
   
   sumx = 0; sumx2=0; avgx =0; rmsx = 0.0;
         for(int j=0;j<EMPeriod+1;j++)
           {
            double r=MathLog(close[in+j]/close[in+j+1]);
            
            sumx+=r;
            sumx2+=r*r;
            
           }
           
         
         if(EMPeriod==0) { avgx=close[in]; rmsx=0.0; }
         else  { avgx=sumx/EMPeriod; rmsx=MathSqrt(sumx2/EMPeriod); }
         
         P = ((avgx/rmsx)+1)/2.0;
         G = P * MathLog(1+rmsx) + (1-P) * MathLog(1-rmsx);
         IndiBuffer[out]=G;
         
        
      in++; out++;
   
       
   }
   return(rates_total);
  }
//+------------------------------------------------------------------+



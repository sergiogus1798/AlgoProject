//+------------------------------------------------------------------+
//|                                                   RSIOnArray.mqh |
//|                                                         lippmaje |
//+------------------------------------------------------------------+
#property copyright "Copyleft 2019, lippmaje"
#property link      "https://www.mql5.com/en/users/lippmaje"
#property version   "1.0"

#define iRSIOnArray RSIOnArray
//+------------------------------------------------------------------+
//| RSIOnArray                                                       |
//+------------------------------------------------------------------+
double RSIOnArray(double &array[],int total,int period,int shift)
  {
   if(total==0)
      total=ArraySize(array);
   int stop=total-shift;
   if(period<=1 || shift<0 || stop<=period)
      return 0;
   bool isSeries=ArrayGetAsSeries(array);
   if(isSeries)
      ArraySetAsSeries(array,false);
   int i;
   double SumP=0;
   double SumN=0;
   for(i=1; i<=period; i++)
     {
      double diff=array[i]-array[i-1];
      if(diff>0)
         SumP+=diff;
      else
         SumN+=-diff;
     }
   if(!MathIsValidNumber(SumP) || !MathIsValidNumber(SumN))
     {
      return MathSqrt(-1);
     }
   double AvgP=SumP/period;
   double AvgN=SumN/period;
   for(; i<stop; i++)
     {
      double diff=array[i]-array[i-1];
      AvgP=(AvgP*(period-1)+(diff>0?diff:0))/period;
      AvgN=(AvgN*(period-1)+(diff<0?-diff:0))/period;
     }
   double rsi;
   if(AvgN==0.0)
     {
      rsi=(AvgP==0.0 ? 50.0 : 100.0);
     }
   else
     {
      rsi=100.0-(100.0/(1.0+AvgP/AvgN));
     }
   if(isSeries)
      ArraySetAsSeries(array,true);
   return rsi;
  }

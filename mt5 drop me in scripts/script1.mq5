#property strict
#property script_show_inputs
#property copyright "PNL Journal History Export"
#property link      "http://127.0.0.1:5000"

input string ApiUrl   = "http://127.0.0.1:5000/api/ingest_trade";
input int    DaysBack = 365;   // how many days to export backward

// -----------------------------
// Helper: send JSON via WebRequest
// -----------------------------
bool SendJson(string url, string json)
{
   uchar data[];
   StringToCharArray(json, data, 0, StringLen(json), CP_UTF8);

   uchar result[];
   string result_headers;
   string headers = "Content-Type: application/json\r\n";
   int timeout = 5000;

   ResetLastError();
   int res = WebRequest("POST", url, headers, timeout, data, result, result_headers);

   if(res == -1)
   {
      int err = GetLastError();
      PrintFormat("WebRequest error (%d). Add URL '%s' to Tools -> Options -> Expert Advisors -> Allow WebRequest.",
                  err, url);
      return false;
   }

   string resp = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("JournalHistoryExport response: ", resp);
   return true;
}

string PriceToStr(double value, int digits)
{
   return DoubleToString(value, digits);
}

string PnlToStr(double value)
{
   return DoubleToString(value, 2);
}

string DateStr(datetime t)
{
   string s = TimeToString(t, TIME_DATE);
   StringReplace(s, ".", "-");
   return s;
}

string TimeStr(datetime t)
{
   return TimeToString(t, TIME_SECONDS);
}

// -----------------------------
// Build and send JSON for one deal/event
// -----------------------------
void SendDealEvent(ulong deal)
{
   long deal_type   = HistoryDealGetInteger(deal, DEAL_TYPE);
   long entry_type  = HistoryDealGetInteger(deal, DEAL_ENTRY);
   double profit    = HistoryDealGetDouble(deal, DEAL_PROFIT);

   string event_type = "";
   string side       = "";
   string symbol     = HistoryDealGetString(deal, DEAL_SYMBOL);
   double volume     = HistoryDealGetDouble(deal, DEAL_VOLUME);
   double price      = HistoryDealGetDouble(deal, DEAL_PRICE);
   double commission = HistoryDealGetDouble(deal, DEAL_COMMISSION);
   double swap       = HistoryDealGetDouble(deal, DEAL_SWAP);
   long   magic      = HistoryDealGetInteger(deal, DEAL_MAGIC);
   string comment    = HistoryDealGetString(deal, DEAL_COMMENT);
   datetime t        = (datetime)HistoryDealGetInteger(deal, DEAL_TIME);

   // classify
   if(deal_type == DEAL_TYPE_BUY || deal_type == DEAL_TYPE_SELL)
   {
      // only closing legs
      if(!(entry_type == DEAL_ENTRY_OUT || entry_type == DEAL_ENTRY_OUT_BY || entry_type == DEAL_ENTRY_INOUT))
         return;

      event_type = "TRADE";
      side       = (deal_type == DEAL_TYPE_BUY ? "LONG" : "SHORT");
   }
   else if(deal_type == DEAL_TYPE_BALANCE)
   {
      symbol = "BAL";
      volume = 0.0;
      price  = 0.0;

      if(profit > 0.0)
      {
         event_type = "DEPOSIT";
         side       = "DEPOSIT";
      }
      else if(profit < 0.0)
      {
         event_type = "WITHDRAWAL";
         side       = "WITHDRAWAL";
      }
      else
      {
         event_type = "BALANCE";
         side       = "BALANCE";
      }
   }
   else if(deal_type == DEAL_TYPE_CORRECTION)
   {
      symbol     = "CORR";
      volume     = 0.0;
      price      = 0.0;
      event_type = "CORRECTION";
      side       = "CORRECTION";
   }
   else if(deal_type == DEAL_TYPE_CHARGE)
   {
      symbol     = "FEE";
      volume     = 0.0;
      price      = 0.0;
      event_type = "FEE";
      side       = "FEE";
   }
   else if(deal_type == DEAL_TYPE_CREDIT)
   {
      symbol     = "CREDIT";
      volume     = 0.0;
      price      = 0.0;
      event_type = "CREDIT";
      side       = "CREDIT";
   }
   else if(deal_type == DEAL_TYPE_BONUS)
   {
      symbol     = "BONUS";
      volume     = 0.0;
      price      = 0.0;
      event_type = "BONUS";
      side       = "BONUS";
   }
   else
   {
      // ignore unknown deal types
      return;
   }

   StringReplace(comment, "\"", "'");

   string date_s = DateStr(t);
   string time_s = TimeStr(t);
   long   ticket = (long)deal;

   int digits = 5;
   if(symbol != "" && SymbolInfoInteger(symbol, SYMBOL_DIGITS) > 0)
      digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   double entry_price = price; // placeholder

   string json = "{";
   json += "\"date\":\""       + date_s + "\",";
   json += "\"time\":\""       + time_s + "\",";
   json += "\"ticket\":"       + (string)ticket + ",";
   json += "\"symbol\":\""     + symbol + "\",";
   json += "\"side\":\""       + side + "\",";
   json += "\"event_type\":\"" + event_type + "\",";
   json += "\"size\":"         + DoubleToString(volume, 2) + ",";
   json += "\"entry\":"        + PriceToStr(entry_price, digits) + ",";
   json += "\"exit\":"         + PriceToStr(price, digits) + ",";
   json += "\"pnl\":"          + PnlToStr(profit) + ",";
   json += "\"chart_url\":\"\",";
   json += "\"commission\":"   + PnlToStr(commission) + ",";
   json += "\"swap\":"         + PnlToStr(swap) + ",";
   json += "\"magic\":"        + (string)magic + ",";
   json += "\"comment\":\""    + comment + "\"";
   json += "}";

   Print("JournalHistoryExport sending JSON: ", json);
   SendJson(ApiUrl, json);
}

// -----------------------------
// Script entry
// -----------------------------
void OnStart()
{
   datetime to   = TimeCurrent();
   datetime from = to - (DaysBack * 86400);

   if(!HistorySelect(from, to))
   {
      Print("HistorySelect failed. Error: ", GetLastError());
      return;
   }

   int total = HistoryDealsTotal();
   PrintFormat("JournalHistoryExport: %d deals in last %d days.", total, DaysBack);

   for(int i = 0; i < total; i++)
   {
      ulong deal_ticket = HistoryDealGetTicket(i);
      if(deal_ticket == 0)
         continue;

      SendDealEvent(deal_ticket);
      Sleep(50);
   }

   Print("JournalHistoryExport finished.");
}

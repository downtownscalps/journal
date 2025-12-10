MT5 Local Trade Journal — Quick Start Instructions

Make sure Python is installed on your system.
If not, download it from python.org and install it.
IMPORTANT: During installation, check the box “Add Python to PATH.”

Unzip the journal folder anywhere you want (Desktop, Downloads, etc.).

Optional: open settings.py to set your starting balance.
Default is 0.
Most brokers report deposits and withdrawals, so 0 is usually correct.

Copy the JournalHistoryExport.mq5 file from the mt5 folder into your MT5 Scripts directory:
MT5 → File → Open Data Folder → MQL5 → Scripts
Then refresh or compile it in the Navigator window.

Start the journal app:
On Windows: double-click run_windows.bat
On Mac: run “chmod +x run_mac.sh” once, then “./run_mac.sh”

Once running, open your browser and go to:
http://127.0.0.1:5000

In MT5, allow WebRequest:
Tools → Options → Expert Advisors → Enable “Allow WebRequest”
Add this URL:
http://127.0.0.1:5000

With your journal app running, drag the JournalHistoryExport script onto any MT5 chart.
It will collect all account history (trades, deposits, withdrawals, fees, etc.)
and send it directly into the journal.

Refresh your browser page.
You should now see your Daily PnL Overview.
Click any day to view all trades and events.

You can re-run the MT5 script anytime.
Duplicate protection is automatic (based on trade ticket numbers).

If you want to reset everything:
Stop the app, delete journal.db, restart the app, re-run the script.

Enjoy your fully local, private MT5 trade journal.
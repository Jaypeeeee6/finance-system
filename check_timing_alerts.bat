@echo off
echo Checking finance approval timing alerts...
cd /d "C:\Users\ysale\finance-system"
python -c "from app import app, db, check_finance_approval_timing_alerts; app.app_context().push(); check_finance_approval_timing_alerts(); print('Timing alerts check completed at', __import__('datetime').datetime.now())"
echo Done.
pause

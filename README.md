# Courtesy notification for interlibrary loans

Ex Libris Alma does not have a built-in functionality for sending reminders of soon to be overdue interlibrary loans made for resource sharing partners (eg. other libraries). This script uses report created in Alma Analytics (GetLendingDueDatesAPI) to build a list of loans overdue within next seven days and sends a notification email.

It is advisable to create a Python virtualenv for running the script.

You likely want to run this script using cron. For an example, to run the script every monday at 7 o'clock, add crontab entry

```
0 7 * * 1 cd directory-of-your-script && directory-of-your-script/bin/python3 send-ill-courtesy-notice.py > send-ill-courtesy-notice.log 2>&1
```

Your GetLendingDueDatesAPI -report should look like following:

![Alma Analytics Report](https://github.com/mjlassila/alma-ill-courtesy-notice/raw/master/analytics-report-screenshot.png "GetLendingDueDatesAPI report in Alma Analytics")

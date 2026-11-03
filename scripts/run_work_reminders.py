"""Optional foreground periodic executor; never installed implicitly."""
import argparse
import logging
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.work_record_service import dispatch_work_reminders


def main():
    parser=argparse.ArgumentParser(description='Internal work reminder executor')
    parser.add_argument('--interval',type=int,default=60)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    if args.interval<10:parser.error('Minimum interval is 10 seconds')
    app=create_app()
    try:
        while True:
            with app.app_context():
                try:
                    count=dispatch_work_reminders()
                    print(f'work reminders: {count} emitted',flush=True)
                except Exception:
                    # Avoid logging record contents, contacts, tokens or DB parameters.
                    logging.error('Work reminder batch failed; pending items will retry.')
                    if args.once:raise SystemExit(1)
            if args.once:return
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('Work reminder executor stopped.',flush=True)


if __name__=='__main__':main()

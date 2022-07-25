import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

parser = argparse.ArgumentParser(description='Generate RL test data')
parser.add_argument('--path', default='.')
parser.add_argument('--start_date', help='Start date (YYYYMMDD)')
parser.add_argument('--end_date', help='End date (YYYYMMDD)')
parser.add_argument('--user', help='User name')
args = parser.parse_args()


def random_30_min_step_count():
    return int(np.random.uniform(0.5, 1000))

def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()

def _uploadGenerator(path, user_id, start_date, end_date):
    pass

def _decisionGenerator(path, user_id, start_date, end_date):
    prompt_times = [(8,30), (12,00), (15,00), (17,30), (20,00)]
    with open(Path(path).joinpath('decision.csv'), 'w') as output_file:
        current_date = start_date
        while current_date < end_date:
            for (h,m) in prompt_times:
                decision_time = datetime(year=current_date.year, 
                                        month=current_date.month, 
                                        day=current_date.day, 
                                        hour=h,
                                        minute=m,
                                        second=0)
                step_count = random_30_min_step_count()
                print(user_id, time_8601(decision_time), step_count)
            
            # output_file.write(f'{user_id},{time_8601(current_date)}\n')
            current_date += timedelta(days=1)

def _updateGenerator(path, user_id, start_date, end_date):
    with open(Path(path).joinpath('update.csv'), 'w') as output_file:
        current_date = start_date
        while current_date < end_date:
            output_file.write(f'{user_id},{time_8601(current_date)}\n')
            current_date += timedelta(days=1)
    
        



if __name__ == '__main__':
    start_date = datetime.strptime(args.start_date, '%Y%m%d')
    end_date = datetime.strptime(args.end_date, '%Y%m%d')
    user_id = args.user
    _updateGenerator(args.path, user_id, start_date, end_date)
    _decisionGenerator(args.path, user_id, start_date, end_date)
    
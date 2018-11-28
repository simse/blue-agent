from rq import Queue
from worker import conn
from apscheduler.schedulers.blocking import BlockingScheduler
from blueagent.run import sync, quick_sync
from blueagent.logger import logger

sched = BlockingScheduler(timezone='Europe/Copenhagen')
q = Queue(connection=conn)
q_high = Queue(connection=conn)


@sched.scheduled_job('interval', seconds=30)
def quick_sync_job():
    q_high.enqueue(quick_sync)


@sched.scheduled_job('interval', minutes=60)
def sync_job():
    q.enqueue(sync)


logger.info("Running full sync before starting...")
sync()

sched.start()

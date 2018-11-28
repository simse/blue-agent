from rq import Queue
from worker import conn
from apscheduler.schedulers.blocking import BlockingScheduler
from blueagent.run import sync

sched = BlockingScheduler()
q = Queue(connection=conn)


@sched.scheduled_job('interval', minutes=1)
def timed_job():
    q.enqueue(sync)


sched.start()

from apscheduler.schedulers.background import BackgroundScheduler

def start_jobs():
    s=BackgroundScheduler(); s.start(); return s

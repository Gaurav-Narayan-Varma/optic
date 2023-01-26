from .helpers import create_nyt_entries, create_wsj_entries

def create_nyt_entries_cron():
    create_nyt_entries()
    
def create_wsj_entries_cron():
    create_wsj_entries()

import multiprocessing

message_q = multiprocessing.Queue(maxsize=0)
job_q = multiprocessing.Queue(maxsize=0)
packet_q = multiprocessing.Queue(maxsize=0)
info_q = multiprocessing.Queue(maxsize=0)

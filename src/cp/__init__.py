from shared.config.locker import Locker
from cp.queue import Queue

locker = Locker()
redis = locker.redis()
queue = Queue(redis).build()


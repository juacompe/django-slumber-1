from slumber._caches import PER_THREAD
from threading import Thread
from time import sleep
from unittest2 import TestCase

class T(Thread):
    def run(self):
        print 'enter run'
        print 'self.name = ', self.name
        PER_THREAD.CACHE = type('cache', (dict,), {})()
        PER_THREAD.CACHE['name'] = self.name
        print 'id = ', id(PER_THREAD.CACHE)
        sleep(10)
        print "PER_THREAD.CACHE['name'] = ", PER_THREAD.CACHE['name']
        print 'exit run'

    def check(self):
        return '%s %s' % (self.name, PER_THREAD.CACHE['name'])

class TestThreadLocalCache(TestCase):

    def test_thread_local_cache(self):
        """
        cache should be separated between threads as IIS is using multi-
        threading to run django application, causing various errors accross the
        system when the system is being used with many concurrent users.
        """
        t1 = T()
        t1.start()
        print 't1 done'
        t2 = T()
        t2.start()
        print 't2 done'
        self.assertEqual('Thread-1 Thread-1', t1.check()) 
        self.assertEqual('Thread-2 Thread-2', t2.check()) 


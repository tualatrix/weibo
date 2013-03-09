#!/usr/bin/env python3

import collections
from PyQt4.QtCore import *
from app import logger

log = logger.getLogger(__name__)

class Thread(QThread):
    def __init__(self, manager, name):
        super(Thread, self).__init__()
        self.manager = manager
        self.name = name
        
    def __str__(self):
        return self.name
        
    def run(self):
        while True:
            try:
                log.debug(self.name + str(self.manager.queue))
                task = self.manager.dequeueTask()
                task.run()
                if task.autoDelete():
                    del task
            except IndexError:
                # There is no task
                log.debug(self.name + 'No task, %s quiting' % self)
                break
            except Exception as e:
                print(e)
                
        self.manager.setThreadIdle(self)

class Manager:
    def __init__(self, max_thread_count):
        self.max_thread_count = max_thread_count
        
        self.threads = [Thread(self, 'thread_%d' % i) for i in range(max_thread_count)]
        
        self.idle_threads = set(self.threads)
        self.idle_threads_mutex = QMutex()
        
        self.queue = collections.deque()
        
    def hasIdleThread(self):
        return len(self.idle_threads) != 0
    
    def setThreadIdle(self, thread):
        self.idle_threads_mutex.lock()
        self.idle_threads.add(thread)
        log.debug('%s becomes idle' % thread)
        self.idle_threads_mutex.unlock()
    
    def startTask(self, task):
        self.enqueueTask(task)
        log.debug('%s enqueued' % task)
        
        self.idle_threads_mutex.lock()
        try:
            thread = self.idle_threads.pop()
            thread.start()
            log.debug('%s started' % task)
        except KeyError:
            # No idle thread
            log.debug('No idle thread')
            pass
        except Exception as e:
            print(e)
        self.idle_threads_mutex.unlock()
    
    def enqueueTask(self, task):
        self.queue.append(task)
    
    def dequeueTask(self):
        return self.queue.popleft()

class ThreadPool:
    def __init__(self, max_thread_count=2):
        self.manager = Manager(max_thread_count)
        
    def start(self, task):
        if not isinstance(task, QRunnable):
            raise TypeError('Task must be QRunnable object.')
        self.manager.startTask(task)
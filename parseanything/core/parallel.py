import concurrent.futures

class ProcessPool:
    def __init__(self, max_workers):
        self.executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
        
    def map(self, func, *iterables):
        return self.executor.map(func, *iterables)
        
    def close(self):
        self.executor.shutdown(wait=True)

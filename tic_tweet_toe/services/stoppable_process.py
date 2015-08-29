from multiprocessing import Process, Event


class StoppableProcess(Process):
    exit = None
    sleep = None

    def __init__(self, sleep=1, *args, **kwargs):
        self.exit = Event()
        self.sleep = sleep
        super(StoppableProcess, self).__init__(*args, **kwargs)

    def _setup(self):
        pass

    def _teardown(self):
        pass

    def _ping(self):
        raise NotImplementedError

    def _should_exit(self):
        return self.exit.wait(0)

    def run(self):
        self._setup()
        while True:
            if self._ping() or self.exit.wait(self.sleep * 1.0):
                self._teardown()
                return

    def stop(self):
        self.exit.set()
        self.join(self.sleep)
        if self.is_alive():
            self.terminate()

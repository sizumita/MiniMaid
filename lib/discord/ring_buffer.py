from collections import deque


class RingBuffer:
    def __init__(self, maxlen=2 ** 12):
        self.queues = {}
        self.maxlen = maxlen

    def append(self, ssrc: int, item: dict):
        if ssrc not in self.queues.keys():
            self.queues[ssrc] = deque(maxlen=self.maxlen)
        self.queues[ssrc].append(item)

    def clear(self):
        self.queues = {}

    def get_all_items(self, after: float):
        """
        get queue items after time
        :param after: float
        :return: List[List[dict]]
        """
        results = []
        for ssrc in list(self.queues)[:15]:
            queue = self.queues[ssrc]
            result = []
            while True:
                try:
                    item = queue.pop()
                    if item['time'] < after:
                        continue
                    result.append(item)
                except IndexError:
                    break
            results += reversed(result)

        return results

class Order:
    total_order = 0

    def __init__(self, before_sequence, position):
        self.id = Order.total_order
        Order.total_order += 1
        self.before_sequence = before_sequence
        self.position = position


class OrderQue:
    def __init__(self):
        self.queue_sequence = []
        self.queue_dict = dict()
        self.max_trade_position = 0

    def add(self, sequence, order):
        self.queue.append(sequence)
        if sequence in self.queue_sequence:
            self.queue_dict[sequence].append(order)
        else:
            self.queue_dict[sequence] = [order]


class Executor:
    def __init__(self):
        self.orders = {}
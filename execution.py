from data_handler import DataHandler
OPEN = 1


class Executor:
    def __init__(self, data_handler):
        self.handler = data_handler
        self.orders = {}

    def fun(self, factor_values):
        len_stocks = len(factor_values)
        rank_stocks = np.array(sorted(range(len_stocks), key=factor_values.__getitem__))
        max_trading_volume = self.handler.get_volume(1)[0] * 0.05
        long_stocks = rank_stocks[:int(len(rank_stocks) / 10)]
        short_stocks = rank_stocks[-int(len(rank_stocks) / 10):]
        delta_position = np.zeros(len_stocks)
        delta_position[long_stocks] = max_trading_volume[long_stocks]
        delta_position[short_stocks] = -max_trading_volume[short_stocks]
        new_direction = np.sign(delta_position)
        old_position = self.handler.position[-1]
        old_direction = np.sign(old_position)
        position = np.where(new_direction == old_direction, old_position + delta_position, old_position)
        position = np.where(position)




        amount = close * position
        while True:
            if np.max(amount) > 0.1 * np.sum(amount) and not isclose(np.max(amount), 0.1 * np.sum(amount),
                                                                     abs_tol=1):
                # logging.info('single:{}'.format(np.max(amount) - 0.1 * np.sum(amount)))
                amount[amount > 0.1 * np.sum(amount)] = 0.1 * np.sum(amount)
                position = amount / close
            amount_long = np.sum(amount[long])
            amount_short = np.sum(amount[short])
            if not isclose(amount_long, amount_short, abs_tol=1):
                # logging.info('exposure:{}'.format(abs(amount_long - amount_short) / (amount_long + amount_short)))
                if amount_long > amount_short:
                    position[long] *= (amount_short / amount_long)
                else:
                    position[short] *= (amount_long / amount_short)
                amount = close * position
            if (np.max(amount) < 0.1 * np.sum(amount) or isclose(np.max(amount), 0.1 * np.sum(amount), abs_tol=1)) and \
                    isclose(np.sum(amount[long]), np.sum(amount[short]), abs_tol=1):
                break
        position[short] *= -1
        return position
from alt_backtest import Indicator


class SMA(Indicator):
    lines = ('sma',)

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.mass = []

    def next(self):
        self.dataclose = self.get_price()
        if len(self.mass) == self.period:
            self.mass.pop(0)
        self.mass.append(self.dataclose)
        self.lines.sma[0] = sum(self.mass) / len(self.mass)

    def is_ready(self) -> bool:
        return len(self.mass) == self.period


class MACDIndicator(Indicator):
    lines = ('macd',)

    def __init__(self, short_period, long_period, period):
        super().__init__()
        self._short_period = short_period
        self._long_period = long_period
        self._period = period

        self._data = []

    def is_ready(self) -> bool:
        return len(self._data) == self._period

    def next(self):
        cur_price = self.get_price()

        if len(self._data) == self._period:
            self._data.pop(0)

        self._data.append(cur_price)
        self.lines.macd[0] = self._ema(self._short_period) - self._ema(self._long_period)


    def _ema(self, period):
        alpha = 2 / (period + 1)
        data_period = self._data[:self._period]
        ema = data_period.pop(0)

        for price in data_period:
            ema = alpha * price + (1 - alpha) * ema

        return ema


class RelativeStrengthIndex(Indicator):
    lines = ('rsi',)

    def __init__(self, period: int):
        super().__init__()
        self.period = period
        self.uperma_n = 0
        self.downrma_n = 0
        self.prev_value = 0
        self.up_diffs = []
        self.down_diffs = []

    def next(self):
        if len(self.up_diffs) == self.period:
            self.up_diffs.pop(0)
            self.down_diffs.pop(0)

        current_price = self.get_price()
        if current_price >= self.prev_value:
            self.up_diffs.append(current_price-self.prev_value)
            self.down_diffs.append(0)
        else:
            self.up_diffs.append(0)
            self.down_diffs.append(self.prev_value - current_price)
        self.prev_value = current_price

        self.uperma_n = sum(self.up_diffs)/self.period
        self.downrma_n = sum(self.down_diffs)/self.period
        if self.downrma_n ==0:
            self.lines.rsi[0] = 100
            return

        rs = self.uperma_n/self.downrma_n
        self.lines.rsi[0]= 100 - 100/(1 + rs)

    def is_ready(self) -> bool:
        return len(self.up_diffs) == self.period
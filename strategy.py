from math import sqrt

from alt_backtest import Strategy, Position, price

from indicators import MACDIndicator, RSI, EMA, SMA
from config import *


class MixedStrategy(Strategy):
    margin = False
    previous = Position.none

    def __init__(self):
        super().__init__()
        self.m_indicator = MACDIndicator(short_period = short_period, long_period = long_period)
        self.r_indicator = RSI(period = rsi_period)
        self.e_short_indicator = EMA(period=short_period)
        self.e_long_indicator = EMA(period=long_period)
        self._sma = SMA(period=msa_period)
        self.k = k
        self.last_mcs = []
        self.last_ema_short = []
        self.last_ema_long = []

        self.min_flet_rsi = min_flet_rsi
        self.max_flet_rsi = max_flet_rsi

        self.long_volume = 0
        self.short_volume = 0

        self.margin_c = 1

        self.max_rsi = max_rsi
        self.min_rsi = min_rsi

        self.rsi_sell = rsi_sell
        self.rsi_buy = rsi_buy

        self.risk = risk
        self.stop_loss = stop_loss

        self.upper_stop_loss = upper_stop_loss

    def get_volume(self, income_price, stop_loss, risk):
        if self.margin:
            self.margin = False
            self.margin_c //= 2
        else:
            self.margin_c = 1

        return (risk * self.get_current_balance() * self.margin_c) / abs(income_price - stop_loss)

    def next(self):
        if not (self.m_indicator.is_ready() and self.r_indicator.is_ready()):
            return

        price = self.get_price()
        self.last_mcs.append(self.m_indicator.macd[0])
        volume = self.get_volume(price, self.stop_loss, self.risk)
        signal = self.m_indicator.ema(self.last_mcs, 0, len(self.last_mcs))

        ml = self._sma.sma[0]
        ub = ml + k * sqrt(sum([(x - ml)**2 for x in self._sma._data]) / msa_period)
        lb = ml - k * sqrt(sum([(x - ml)**2 for x in self._sma._data]) / msa_period)


        if not self.in_position():
            if self.min_flet_rsi < self.r_indicator.rsi[0] < self.max_flet_rsi and lb <= price <= ub:
                if self.r_indicator.rsi[0] <= self.min_rsi:
                    self.send_market_order_buy(size = volume)
                    self.long_volume += volume
                    self.position_status = Position.long
                    return
                elif self.r_indicator.rsi[0] >= self.max_rsi:
                    self.send_market_order_sell(size = volume)
                    self.short_volume += volume
                    self.position_status = Position.short
                return
            else:

                if self.m_indicator.macd[0] > signal and self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0]:
                    self.send_market_order_buy(size = volume)
                    self.long_volume += volume
                    self.position_status = Position.long
                    return
                elif self.m_indicator.macd[0] < signal and self.e_short_indicator.ema[0] < self.e_long_indicator.ema[0]:
                    self.send_market_order_sell(size = volume)
                    self.position_status = Position.short
                    self.short_volume += volume
                return

        if self.position_status == Position.long:
            if price <= stop_loss:
                self.send_market_order_sell(size = self.long_volume)
                self.previous = self.position_status
                self.long_volume = 0
                self.position_status = Position.none
                return

            if self.min_flet_rsi < self.r_indicator.rsi[0] < self.max_flet_rsi and lb <= price <= ub:
                if self.r_indicator.rsi[0] >= self.rsi_sell:
                    self.send_market_order_sell(size = volume)
                    self.long_volume -= volume
                    self.previous = self.position_status
                    self.position_status = Position.none
                    return
            else:
                signal = self.m_indicator.ema(self.last_mcs, 0, len(self.last_mcs))

                if self.m_indicator.macd[0] < signal and self.e_short_indicator.ema[0] < self.e_long_indicator.ema[0]:
                    self.send_market_order_sell(size = volume)
                    self.long_volume -= volume
                    self.position_status = Position.none
                    return

        if self.position_status == Position.short:
            if price >= self.upper_stop_loss:
                self.send_market_order_buy(size = self.short_volume)
                self.previous = self.position_status
                self.short_volume = 0
                self.position_status = Position.none
                return

            if self.min_flet_rsi < self.r_indicator.rsi[0] < self.max_flet_rsi and lb <= price <= ub:
                if self.r_indicator.rsi[0] >= self.rsi_sell:
                    self.send_market_order_buy(size = volume)
                    self.previous = self.position_status
                    self.short_volume -= volume
                    self.position_status = Position.none
                    return

            else:
                if self.m_indicator.macd[0] > signal and self.e_short_indicator.ema[0] > self.e_long_indicator.ema[0]:
                    self.send_market_order_buy(size = volume)
                    self.previous = self.position_status
                    self.short_volume -= volume
                    self.position_status = Position.none
                    return

    def margin_call(self):
        self.margin = True
        volume = self.get_volume(self.get_price(), self.stop_loss, self.risk)

        if self.previous == Position.long:
            self.long_volume += volume
            self.send_market_order_buy(size = volume)
        else:
            self.short_volume += volume
            self.send_market_order_sell(size = volume)
















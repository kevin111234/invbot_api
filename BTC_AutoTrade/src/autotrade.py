import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np
from itertools import product

# 1. 데이터 수집
def get_data(symbol='BTC-USD', start='2020-01-01', end='2023-09-30'):
    data = yf.download(symbol, start=start, end=end)
    data.reset_index(inplace=True)
    data['Datetime'] = pd.to_datetime(data['Date'])
    return data

# 데이터 로드
data_df = get_data()

# 2. 전략 클래스 정의
class ImprovedStrategy(bt.Strategy):
    params = dict(
        ema_short=12,
        ema_long=26,
        rsi_period=14,
        bb_period=20,
        bb_dev=2,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        atr_period=14,
        weight_ema=0.3,
        weight_rsi=0.2,
        weight_bb=0.2,
        weight_macd=0.3,
        buy_threshold=0.3,
        sell_threshold=-0.3,
        stop_loss_atr_multiplier=1.5,  # 최적화 대상
        take_profit_atr_multiplier=3.0  # 최적화 대상
    )
    
    def __init__(self):
        self.ema_short = bt.ind.EMA(self.data.close, period=self.p.ema_short)
        self.ema_long = bt.ind.EMA(self.data.close, period=self.p.ema_long)
        self.rsi = bt.ind.RSI(self.data.close, period=self.p.rsi_period)
        self.bb = bt.ind.BollingerBands(self.data.close, period=self.p.bb_period, devfactor=self.p.bb_dev)
        self.macd = bt.ind.MACD(self.data.close, period_me1=self.p.macd_fast, period_me2=self.p.macd_slow, period_signal=self.p.macd_signal)
        self.atr = bt.ind.ATR(self.data, period=self.p.atr_period)
        
        self.buy_price = None
        self.stop_price = None
        self.take_price = None
        
    def next(self):
        score = 0
        
        # EMA 교차 신호
        if self.ema_short > self.ema_long:
            score += 1 * self.p.weight_ema
        elif self.ema_short < self.ema_long:
            score -= 1 * self.p.weight_ema
        
        # RSI 신호
        if self.rsi < 30:
            score += 1 * self.p.weight_rsi
        elif self.rsi > 70:
            score -= 1 * self.p.weight_rsi
        
        # 볼린저 밴드 신호
        if self.data.close < self.bb.bot:
            score += 1 * self.p.weight_bb
        elif self.data.close > self.bb.top:
            score -= 1 * self.p.weight_bb
        
        # MACD 신호
        if self.macd.macd > self.macd.signal:
            score += 1 * self.p.weight_macd
        elif self.macd.macd < self.macd.signal:
            score -= 1 * self.p.weight_macd
        
        # 매수 신호
        if score >= self.p.buy_threshold and not self.position:
            if not np.isnan(self.atr[0]):
                self.buy()
                self.buy_price = self.data.close[0]
                self.stop_price = self.buy_price - self.atr[0] * self.p.stop_loss_atr_multiplier
                self.take_price = self.buy_price + self.atr[0] * self.p.take_profit_atr_multiplier
                print(f"Buy signal on {self.data.datetime.date(0)}: Price={self.buy_price}, Stop={self.stop_price}, Take={self.take_price}")
        
        # 매도 신호
        elif score <= self.p.sell_threshold and self.position:
            self.sell()
            print(f"Sell signal on {self.data.datetime.date(0)}: Price={self.data.close[0]}")
            self.buy_price = None
            self.stop_price = None
            self.take_price = None
        
        # 리스크 관리 (스탑로스 및 테이크프로핏)
        if self.position:
            current_price = self.data.close[0]
            if self.stop_price is not None and current_price <= self.stop_price:
                self.sell()
                print(f"Stop loss triggered on {self.data.datetime.date(0)}: Price={current_price}")
                self.buy_price = None
                self.stop_price = None
                self.take_price = None
            elif self.take_price is not None and current_price >= self.take_price:
                self.sell()
                print(f"Take profit triggered on {self.data.datetime.date(0)}: Price={current_price}")
                self.buy_price = None
                self.stop_price = None
                self.take_price = None

# 3. 성과 분석을 위한 커스텀 애널라이저 정의
class CustomTradeAnalyzer(bt.Analyzer):
    def __init__(self):
        self.trade_records = []
    
    def notify_trade(self, trade):
        if trade.isclosed:
            # 수익률 계산 (포트폴리오 기준)
            profit_ratio = trade.pnl / trade.price if trade.price != 0 else 0
            self.trade_records.append({
                'profit': profit_ratio
            })
    
    def get_analysis(self):
        total_trades = len(self.trade_records)
        winning_trades = len([t for t in self.trade_records if t['profit'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        returns = [t['profit'] for t in self.trade_records]
        total_return = np.sum(returns) * 100
        
        if returns:
            cumulative = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = running_max - cumulative
            max_drawdown = np.max(drawdowns) * 100 if len(drawdowns) > 0 else 0
        else:
            max_drawdown = 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'max_drawdown': max_drawdown
        }

# 4. 백테스트 실행 및 결과 출력
class PandasData(bt.feeds.PandasData):
    params = (
        ('datetime', 'Datetime'),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', None),
    )

data_feed = PandasData(dataname=data_df)

# 5. 그리드 서치를 통한 전략 최적화
def grid_search(data_feed, weight_ema_candidates, weight_rsi_candidates, weight_bb_candidates, weight_macd_candidates, 
                buy_threshold_candidates, sell_threshold_candidates, stop_loss_candidates, take_profit_candidates):
    best_return = -np.inf
    best_params = None
    best_trade_analyzer = None
    best_drawdown = None
    
    for weight_ema, weight_rsi, weight_bb, weight_macd, buy_threshold, sell_threshold, stop_loss, take_profit in product(
        weight_ema_candidates, weight_rsi_candidates, weight_bb_candidates, weight_macd_candidates, 
        buy_threshold_candidates, sell_threshold_candidates, stop_loss_candidates, take_profit_candidates):
        
        if not np.isclose(weight_ema + weight_rsi + weight_bb + weight_macd, 1.0):
            continue
        
        cerebro_opt = bt.Cerebro()
        cerebro_opt.adddata(data_feed)
        cerebro_opt.addstrategy(
            ImprovedStrategy,
            weight_ema=weight_ema,
            weight_rsi=weight_rsi,
            weight_bb=weight_bb,
            weight_macd=weight_macd,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold,
            stop_loss_atr_multiplier=stop_loss,
            take_profit_atr_multiplier=take_profit
        )
        cerebro_opt.broker.setcash(1000000)
        cerebro_opt.broker.setcommission(commission=0.001)
        
        # 애널라이저 추가
        cerebro_opt.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro_opt.addanalyzer(CustomTradeAnalyzer, _name='customtradeanalyzer')
        
        result_opt = cerebro_opt.run()
        final_value = cerebro_opt.broker.getvalue()
        
        # 최적의 파라미터 업데이트
        if final_value > best_return:
            best_return = final_value
            best_params = {
                'weight_ema': weight_ema,
                'weight_rsi': weight_rsi,
                'weight_bb': weight_bb,
                'weight_macd': weight_macd,
                'buy_threshold': buy_threshold,
                'sell_threshold': sell_threshold,
                'stop_loss_atr_multiplier': stop_loss,
                'take_profit_atr_multiplier': take_profit
            }
            best_trade_analyzer = result_opt[0].analyzers.customtradeanalyzer.get_analysis()
            best_drawdown = result_opt[0].analyzers.drawdown.get_analysis()
    
    return best_params, best_return, best_trade_analyzer, best_drawdown

# 그리드 서치 파라미터 설정
weight_ema_candidates = [0.2, 0.3, 0.4]
weight_rsi_candidates = [0.1, 0.2, 0.3]
weight_bb_candidates = [0.2, 0.3, 0.4]
weight_macd_candidates = [0.2, 0.3, 0.4]
buy_threshold_candidates = [0.2, 0.3, 0.4]
sell_threshold_candidates = [-0.2, -0.3, -0.4]
stop_loss_candidates = [1.0, 1.5, 2.0]
take_profit_candidates = [2.0, 3.0, 4.0]

# 최적의 파라미터 탐색
best_params, best_return, best_trade_analyzer, best_drawdown = grid_search(
    data_feed,
    weight_ema_candidates,
    weight_rsi_candidates,
    weight_bb_candidates,
    weight_macd_candidates,
    buy_threshold_candidates,
    sell_threshold_candidates,
    stop_loss_candidates,
    take_profit_candidates
)

# 최적의 파라미터 및 성과 출력
print("\n최적의 파라미터 조합:")
for param, value in best_params.items():
    print(f"  {param}: {value}")
print(f"최적의 포트폴리오 가치: {best_return:.2f}")

print("\n최적의 파라미터로 얻은 성과:")
print(f"  Total Trades: {best_trade_analyzer['total_trades']}")
print(f"  Win Rate: {best_trade_analyzer['win_rate']:.2f}%")
print(f"  Total Return: {best_trade_analyzer['total_return']:.2f}%")
print(f"  Max Drawdown: {best_trade_analyzer['max_drawdown']:.2f}%")

import numpy as np
import pandas as pd
from itertools import product
import pyupbit

# 1. 데이터 로드 (PyUpbit API로 5분 봉 데이터 수집)
def get_data(symbol='KRW-BTC', interval='minute5', count=70000):
    df = pyupbit.get_ohlcv(symbol, interval=interval, count=count)
    df = df.reset_index()
    return df

data = get_data()

# RSI 계산 함수
def compute_rsi(series, period):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# 볼린저 밴드 계산 함수
def compute_bollinger_bands(series, period, num_std=2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + num_std * std
    lower_band = sma - num_std * std
    return upper_band, lower_band

# 백테스트 전략 함수 (수정된 버전)
def backtest_strategy(data, ema_short, ema_long, rsi_period, bb_period, stop_loss, take_profit):
    cash = 1000000  # 초기 자본
    initial_cash = cash
    position = None  # 현재 포지션 정보
    total_trades = 0
    win_trades = 0
    losses = []
    max_drawdown = 0
    peak_value = cash
    fee_rate = 0.0005  # 수수료 0.05%

    # 지표 계산
    data['ema_short'] = data['close'].ewm(span=ema_short, adjust=False).mean()
    data['ema_long'] = data['close'].ewm(span=ema_long, adjust=False).mean()
    data['rsi'] = compute_rsi(data['close'], rsi_period)
    data['bb_upper'], data['bb_lower'] = compute_bollinger_bands(data['close'], bb_period)

    for index, row in data.iterrows():
        current_price = row['close']

        # 총 자산 가치 계산
        total_asset = cash
        if position is not None:
            total_asset += position['quantity'] * current_price

        # MDD 계산
        if total_asset > peak_value:
            peak_value = total_asset
        drawdown = (peak_value - total_asset) / peak_value * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        # 매수 조건
        if (row['ema_short'] > row['ema_long']) and (row['rsi'] < 30) and (current_price <= row['bb_lower']):
            if position is None:
                # 전액 매수
                position_quantity = (cash * (1 - fee_rate)) / current_price
                position_price = current_price
                position = {
                    'quantity': position_quantity,
                    'price': position_price,
                    'stop_price': position_price * (1 - stop_loss),
                    'take_price': position_price * (1 + take_profit)
                }
                cash = 0
                total_trades += 1
                # print(f"매수: 가격={current_price}, 손절가={position['stop_price']}, 이익실현가={position['take_price']}")

        # 매도 조건
        elif position is not None:
            if current_price >= position['take_price']:
                # 이익 실현 매도
                sell_value = position['quantity'] * current_price * (1 - fee_rate)
                profit = sell_value - (position['quantity'] * position['price'])
                cash += sell_value
                win_trades += 1
                # print(f"이익 실현 매도: 가격={current_price}, 현금={cash}")
                position = None
            elif current_price <= position['stop_price']:
                # 손절 매도
                sell_value = position['quantity'] * current_price * (1 - fee_rate)
                loss = (position['quantity'] * position['price']) - sell_value
                cash += sell_value
                losses.append(loss / (position['quantity'] * position['price']) * 100)
                # print(f"손절 매도: 가격={current_price}, 현금={cash}")
                position = None

    # 최종 자산 가치 계산
    if position is not None:
        total_asset = cash + position['quantity'] * current_price
    else:
        total_asset = cash

    # 성과 지표 계산
    total_return = (total_asset - initial_cash) / initial_cash * 100
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

    return data, total_asset, max_drawdown, total_trades, win_rate, total_return

# 그리드 서치 함수
def grid_search(data, ema_short_candidates, ema_long_candidates, rsi_period_candidates, bb_period_candidates, stop_loss_candidates, take_profit_candidates):
    best_portfolio_value = -np.inf
    best_params = None
    best_results = None

    for ema_short, ema_long, rsi_period, bb_period, stop_loss, take_profit in product(
            ema_short_candidates, ema_long_candidates, rsi_period_candidates, bb_period_candidates, stop_loss_candidates, take_profit_candidates):

        # 백테스트 실행
        results, portfolio_value, mdd, total_trades, win_rate, total_return = backtest_strategy(
            data.copy(), ema_short, ema_long, rsi_period, bb_period, stop_loss, take_profit)

        if portfolio_value > best_portfolio_value:
            best_portfolio_value = portfolio_value
            best_params = {
                'ema_short': ema_short,
                'ema_long': ema_long,
                'rsi_period': rsi_period,
                'bb_period': bb_period,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
            best_results = {
                'portfolio_value': portfolio_value,
                'mdd': mdd,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_return': total_return
            }

    return best_params, best_results

# 그리드 서치 파라미터 설정
ema_short_candidates = [10, 15]
ema_long_candidates = [20, 30]
rsi_period_candidates = [14, 21]
bb_period_candidates = [10, 20]
stop_loss_candidates = [0.01, 0.1]
take_profit_candidates = [0.02, 0.2]

# 그리드 서치 실행
best_params, best_results = grid_search(
    data,
    ema_short_candidates,
    ema_long_candidates,
    rsi_period_candidates,
    bb_period_candidates,
    stop_loss_candidates,
    take_profit_candidates
)

# 결과 출력
print(f"최적의 파라미터 조합: {best_params}")
print(f"최종 포트폴리오 가치: {best_results['portfolio_value']}")
print(f"최대 낙폭(MDD): {best_results['mdd']}%")
print(f"총 거래 횟수: {best_results['total_trades']}")
print(f"승률: {best_results['win_rate']}%")
print(f"총 수익률: {best_results['total_return']}%")

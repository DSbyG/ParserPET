import os
import pandas as pd
import requests
import csv
from .telegram_notifications import send_telegram_message

def coins_in_fast_bullish_divergence(df):
    fast_bullish_df = df[df.apply(lambda row: any(0 <= row[timeframe] < 15 for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']), axis=1)]
    if not fast_bullish_df.empty:
        for coin in fast_bullish_df['Coin']:
            message = f"Монета {coin} в зоне быстрого поиска бычьего дивера."
            send_telegram_message(message)
    return fast_bullish_df

def coins_in_fast_bearish_divergence(df):
    fast_bearish_df = df[df.apply(lambda row: any(85 < row[timeframe] <= 100 for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']), axis=1)]
    if not fast_bearish_df.empty:
        for coin in fast_bearish_df['Coin']:
            message = f"Монета {coin} в зоне быстрого поиска медвежьего дивера."
            send_telegram_message(message)
    return fast_bearish_df

def fetch_futures_coins():
    url = 'https://cvizor.com/api/v1/screener/settings'
    response = requests.get(url)
    data = response.json()
    futures_coins = [pair['symbol'] for pair in data['pairs'] if pair['is_futures']]
    return futures_coins

def fetch_data_from_api():
    url = 'https://cvizor.com/api/v2/screener/tables'
    response = requests.get(url)
    data = response.json()
    return data

def parse_data(data, coins):
    intervals = data['intervals']
    rsi14_values = {}

    for coin_data in data['data']:
        for coin in coins:
            if coin_data['coin']['label'] == coin:
                coin_label = coin_data['coin']['label']
                rsi14_values[coin_label] = {}
                for interval in intervals:
                    if interval in coin_data:
                        rsi14_values[coin_label][interval] = coin_data[interval]['rsi14']

    return rsi14_values, intervals

def save_parsed_data(rsi14_values, intervals):
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values.csv')
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ['Coin'] + intervals
        writer.writerow(header)
        for coin, rsi_values in rsi14_values.items():
            row = [coin] + [rsi_values.get(interval, '') for interval in intervals]
            writer.writerow(row)

def load_data():
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values.csv')
    return pd.read_csv(file_path)

def save_data(df):
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values_with_zones.csv')
    df.to_csv(file_path, index=False)

def classify_rsi_zone(rsi):
    try:
        rsi = float(rsi)
    except ValueError:
        return 'Неизвестная зона'
    if 0 <= rsi < 50:
        return 'Красная зона'
    elif 50 <= rsi <= 55:
        return 'Бежевая зона'
    elif 55 < rsi <= 100:
        return 'Зеленая зона'
    return 'Неизвестная зона'

def classify_divergence_zone(rsi):
    try:
        rsi = float(rsi)
    except ValueError:
        return 'Боковик/Слабый тренд'
    if 0 <= rsi < 30:
        return 'Зона бычьего дивера'
    elif 70 < rsi <= 100:
        return 'Зона медвежьего дивера'
    elif 0 <= rsi < 15:
        return 'Зона быстрого поиска бычьего дивера'
    elif 85 < rsi <= 100:
        return 'Зона быстрого поиска медвежьего дивера'
    return 'Боковик/Слабый тренд'

def add_rsi_zones(df):
    for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']:
        df[timeframe] = pd.to_numeric(df[timeframe], errors='coerce')
        df[f'{timeframe}_zone'] = df[timeframe].apply(classify_rsi_zone)
        df[f'{timeframe}_divergence'] = df[timeframe].apply(classify_divergence_zone)
    return df

def calculate_divergence_percentages(df):
    total_coins = len(df)
    percentages = {'timeframe': [], 'bullish_divergence': [], 'bearish_divergence': []}
    
    for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']:
        bullish_count = df[f'{timeframe}_divergence'].value_counts().get('Зона бычьего дивера', 0)
        bearish_count = df[f'{timeframe}_divergence'].value_counts().get('Зона медвежьего дивера', 0)
        
        percentages['timeframe'].append(timeframe)
        percentages['bullish_divergence'].append((bullish_count / total_coins) * 100)
        percentages['bearish_divergence'].append((bearish_count / total_coins) * 100)
    
    return pd.DataFrame(percentages)

def coins_in_long_zone(df):
    result = []
    for index, row in df.iterrows():
        bullish_timeframes = []
        for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']:
            if row[f'{timeframe}_divergence'] == 'Зона бычьего дивера':
                bullish_timeframes.append(timeframe)
        if len(bullish_timeframes) >= 2:
            result.append((row['Coin'], bullish_timeframes))
    return result

def coins_in_short_zone(df):
    short_coins = []
    for index, row in df.iterrows():
        bearish_timeframes = []
        for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']:
            if row[f'{timeframe}_divergence'] == 'Зона медвежьего дивера':
                bearish_timeframes.append(timeframe)
        if len(bearish_timeframes) >= 2:
            short_coins.append((row['Coin'], bearish_timeframes))
    return short_coins


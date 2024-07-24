import os
import pandas as pd
import requests
import csv

def fetch_futures_coins():
    """
    Function to fetch futures coins from Cvizor.
    """
    url = 'https://cvizor.com/api/v1/screener/settings'
    response = requests.get(url)
    data = response.json()
    futures_coins = [pair['symbol'] for pair in data['pairs'] if pair['is_futures']]
    return futures_coins

def fetch_data_from_api():
    """
    Function to fetch data from the API.
    """
    url = 'https://cvizor.com/api/v2/screener/tables'
    response = requests.get(url)
    data = response.json()
    return data

def parse_data(data, coins):
    """
    Function to parse the data and extract RSI14 values for futures coins.
    """
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
    """
    Function to save parsed RSI14 values to a CSV file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values.csv')
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        header = ['Coin'] + intervals
        writer.writerow(header)
        for coin, rsi_values in rsi14_values.items():
            row = [coin] + [rsi_values.get(interval, '') for interval in intervals]
            writer.writerow(row)

def load_data():
    """
    Function to load data from a predefined CSV file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values.csv')
    return pd.read_csv(file_path)

def save_data(df):
    """
    Function to save data to a predefined CSV file.
    """
    file_path = os.path.join(os.path.dirname(__file__), '../data/rsi14_values_with_zones.csv')
    df.to_csv(file_path, index=False)

def classify_rsi_zone(rsi):
    """
    Function to classify RSI zone.
    """
    if 0 <= rsi < 50:
        return 'Красная зона'
    elif 50 <= rsi <= 55:
        return 'Бежевая зона'
    elif 55 < rsi <= 100:
        return 'Зеленая зона'
    return 'Неизвестная зона'

def classify_divergence_zone(rsi):
    """
    Function to classify divergence zone based on RSI value.
    """
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
    """
    Add RSI zones and divergence zones to DataFrame.
    """
    for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']:
        df[f'{timeframe}_zone'] = df[timeframe].apply(classify_rsi_zone)
        df[f'{timeframe}_divergence'] = df[timeframe].apply(classify_divergence_zone)
    return df

def calculate_divergence_percentages(df):
    """
    Calculate the percentage of coins in bullish and bearish divergence zones.
    """
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
    """
    Determine which coins are in bullish divergence zone for at least two timeframes.
    """
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
    """
    Function to identify coins in bearish divergence zone for at least two timeframes
    
    Функция для определения монет в зоне медвежьей дивергенции по крайней мере для двух таймфреймов
    """
    short_coins = []

    for coin, group in df.groupby('Coin'):
        count = sum(group[f'{timeframe}_divergence'].iloc[0] == 'Зона медвежьего дивера' for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d'])
        if count >= 2:
            short_coins.append((coin, [timeframe for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d'] if group[f'{timeframe}_divergence'].iloc[0] == 'Зона медвежьего дивера']))

    return short_coins

def coins_in_fast_bullish_divergence(df):
    """
    Function to identify coins in fast bullish divergence zone for any timeframe
    
    Функция для определения монет в зоне быстрого поиска бычьей дивергенции для любого таймфрейма
    """
    fast_bullish_coins = df[df.apply(lambda row: any(row[f'{timeframe}_divergence'] == 'Зона быстрого поиска бычьего дивера' for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']), axis=1)]
    return fast_bullish_coins

def coins_in_fast_bearish_divergence(df):
    """
    Function to identify coins in fast bearish divergence zone for any timeframe
    
    Функция для определения монет в зоне быстрого поиска медвежьей дивергенции для любого таймфрейма
    """
    fast_bearish_coins = df[df.apply(lambda row: any(row[f'{timeframe}_divergence'] == 'Зона быстрого поиска медвежьего дивера' for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']), axis=1)]
    return fast_bearish_coins
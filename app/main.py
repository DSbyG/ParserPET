import sys
import os
import streamlit as st
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

load_dotenv()

# Добавляем путь к директории ParserPET в системный путь Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.data_processing import load_data, add_rsi_zones, save_data, fetch_futures_coins, fetch_data_from_api, parse_data, save_parsed_data, coins_in_long_zone, coins_in_short_zone, coins_in_fast_bullish_divergence, coins_in_fast_bearish_divergence
from app.ui import show_data, show_divergence_with_progress, show_long_zone_coins, show_short_zone_coins, show_fast_divergence_table, show_page

@st.cache_data
def get_data_from_api():
    futures_coins = fetch_futures_coins()  # Получаем фьючерсные монеты
    data = fetch_data_from_api()  # Получаем данные из API
    rsi14_values, intervals = parse_data(data, futures_coins)  # Парсим данные
    save_parsed_data(rsi14_values, intervals)  # Сохраняем данные в CSV файл
    df = load_data()  # Загружаем данные из сохраненного CSV файла
    df = add_rsi_zones(df)  # Добавляем зоны RSI и дивергенции
    save_data(df)  # Сохраняем измененные данные
    return df

@st.cache_data(ttl=300)  # Данные кэшируются на 5 минут
def get_cached_data():
    return get_data_from_api()

def main():
    st.title("RSI Zones and Divergence Analysis")

    # Показ последнего обновления
    last_update = st.empty()
    df = get_cached_data()
    last_update.text(f"Последнее обновление: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Навигация по страницам
    page = st.sidebar.selectbox("Выберите страницу", 
                                ['Бычья дивергенция', 'Медвежья дивергенция', 'ТВХ в лонг', 'ТВХ в шорт', 'Быстрый поиск бычьего дивера', 'Быстрый поиск медвежьего дивера'])

    show_page(page, df)

    # Рассчитываем время до следующего обновления данных
    now = datetime.utcnow()
    next_update = (now + timedelta(minutes=5 - now.minute % 5)).replace(second=0, microsecond=0)
    sleep_time = (next_update - now).total_seconds()
    
    # Ожидаем время до начала новой свечи
    time.sleep(sleep_time)
    st.rerun()

if __name__ == "__main__":
    main()

import streamlit as st
from .data_processing import load_data, add_rsi_zones, save_data, calculate_divergence_percentages, coins_in_long_zone, coins_in_short_zone, coins_in_fast_bullish_divergence, coins_in_fast_bearish_divergence

def show_data(df):
    """
    Display data in Streamlit.
    
    :param df: DataFrame с данными
    """
    st.dataframe(df)

def show_divergence_with_progress(df, divergence_type='bullish'):
    """
    Display divergence percentages and coins in divergence zone with progress bars in Streamlit.
    
    :param df: DataFrame с данными
    :param divergence_type: 'bullish' or 'bearish' to indicate the type of divergence
    """
    percentages_df = calculate_divergence_percentages(df)
    timeframes = ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']
    
    for timeframe in timeframes:
        if divergence_type == 'bullish':
            percentage = percentages_df[percentages_df['timeframe'] == timeframe]['bullish_divergence'].values[0]
            divergence_coins = df[df[f'{timeframe}_divergence'] == 'Зона бычьего дивера']['Coin'].str.replace('USDT', '').tolist()
            bar_color = 'green'
            coin_color = 'green'
        else:
            percentage = percentages_df[percentages_df['timeframe'] == timeframe]['bearish_divergence'].values[0]
            divergence_coins = df[df[f'{timeframe}_divergence'] == 'Зона медвежьего дивера']['Coin'].str.replace('USDT', '').tolist()
            bar_color = 'red'
            coin_color = 'red'
        
        st.markdown(f"<h3 style='font-size:24px;'>{timeframe}</h3>", unsafe_allow_html=True)
        st.write(f"{percentage:.2f}% в зоне {'бычьей' if divergence_type == 'bullish' else 'медвежьей'} дивергенции.")
        
        # Display progress bar with custom color
        st.progress(percentage / 100)
        st.markdown(f"""
            <style>
            .stProgress > div > div > div > div {{
                background-color: {bar_color};
            }}
            </style>""", unsafe_allow_html=True)
        
        if divergence_coins:
            colored_coins = ', '.join([f"<span style='color:{coin_color}'>{coin}</span>" for coin in divergence_coins])
            st.markdown(f"Монеты: {colored_coins}", unsafe_allow_html=True)
        else:
            st.write("Нет монет в зоне дивергенции.")

def show_long_zone_coins(coins):
    """
    Display coins that are in the bullish divergence zone for at least two timeframes.
    
    :param coins: list of tuples with coin and timeframes
    """
    if not coins:
        st.write("Нет монет в зоне бычьей дивергенции по двум или более таймфреймам.")
    else:
        for coin, timeframes in coins:
            st.write(f"Монета {coin} в зоне бычьей дивергенции по таймфреймам: {', '.join(timeframes)}")

def show_short_zone_coins(coins):
    """
    Display coins that are in the bearish divergence zone for at least two timeframes.
    
    :param coins: list of tuples with coin and timeframes
    """
    if not coins:
        st.write("Нет монет в зоне медвежьей дивергенции по двум или более таймфреймам.")
    else:
        for coin, timeframes in coins:
            st.write(f"Монета {coin} в зоне медвежьей дивергенции по таймфреймам: {', '.join(timeframes)}")

def show_fast_divergence_table(df, divergence_type='bullish'):
    """
    Display table of coins in fast divergence zones
    
    :param df: DataFrame с данными
    :param divergence_type: 'bullish' or 'bearish' to indicate the type of divergence
    """
    if divergence_type == 'bullish':
        fast_coins_df = coins_in_fast_bullish_divergence(df)
    else:
        fast_coins_df = coins_in_fast_bearish_divergence(df)
    
    if fast_coins_df.empty:
        st.write(f"No coins in fast {divergence_type} divergence zone.")
        return
    
    def highlight_cells(val, divergence_type):
        color = 'green' if divergence_type == 'bullish' else 'red'
        return f'background-color: {color}' if 'быстрого поиска' in val else ''
    
    styled_df = fast_coins_df.style.applymap(lambda val: highlight_cells(val, divergence_type), subset=[f'{timeframe}_divergence' for timeframe in ['5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']])
    st.dataframe(styled_df)

def show_page(page, df):
    """
    Display the selected page.
    
    :param page: selected page
    :param df: DataFrame с данными
    """
    if page == 'Бычья дивергенция':
        show_divergence_with_progress(df, divergence_type='bullish')
    elif page == 'Медвежья дивергенция':
        show_divergence_with_progress(df, divergence_type='bearish')
    elif page == 'ТВХ в лонг':
        coins = coins_in_long_zone(df)
        show_long_zone_coins(coins)
    elif page == 'ТВХ в шорт':
        coins = coins_in_short_zone(df)
        show_short_zone_coins(coins)
    elif page == 'Быстрый поиск бычьего дивера':
        show_fast_divergence_table(df, divergence_type='bullish')
    elif page == 'Быстрый поиск медвежьего дивера':
        show_fast_divergence_table(df, divergence_type='bearish')

import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

##########Load the data from the database.############

DB_HOST = st.secrets['DB_HOST']
DB_NAME = st.secrets['DB_NAME']
DB_USER = st.secrets['DB_USER']
DB_PASS = st.secrets['DB_PASSWORD']
DB_PORT = st.secrets['DB_PORT']

# Show the page title and description.
st.set_page_config(page_title="Cryptocurrency Data Set", page_icon="💰" , layout="wide")

#cache the data so it doesn't have to be reloaded every time the page is refreshed
@st.cache_data
def load_data():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    query = "SELECT * FROM student.am_capstone_cryptocurrency_data"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


df = load_data()

df_graph = df.copy()

######### Data Processing #########

# Convert 'last_updated' to datetime.date for comparison
df['last_updated'] = pd.to_datetime(df['last_updated']).dt.date.copy()

# Define today and yesterday
today = datetime.now().date()
yesterday = today - timedelta(days=1)

# Filter for today's and yesterday's data
df_today = df.query("last_updated == @today")
df_yesterday = df.query("last_updated == @yesterday")

# Get the most recent current price for today
df_today_latest = df_today.sort_values(by=['symbol', 'last_updated']).drop_duplicates('symbol', keep='last')

# Calculate yesterday's average price
avg_prices_yesterday = df_yesterday.groupby('symbol', as_index=False)['current_price'].mean().rename(columns={'current_price': 'avg_price_yesterday'})

# Merge and calculate the percentage change
comparison_df = pd.merge(df_today_latest[['symbol', 'current_price']], avg_prices_yesterday, on='symbol')
comparison_df['percentage_change'] = ((comparison_df['current_price'] - comparison_df['avg_price_yesterday']) / comparison_df['avg_price_yesterday']) * 100

# Function to format percentage change with color, arrow, and include current price
def format_display(row):
    change_indicator = "▲" if row['percentage_change'] > 0 else "▼"
    color = "green" if row['percentage_change'] > 0 else "red"
    return f"{row['symbol']}: ${row['current_price']} <span style='color:{color};'>({change_indicator} {abs(row['percentage_change']):.2f}%)</span>"

# Sort the DataFrame by 'percentage_change' in descending order to get biggest gains first
comparison_df_sorted = comparison_df.sort_values(by='percentage_change', ascending=False)

# Apply the format_display function to the DataFrame
comparison_df_sorted['display'] = comparison_df_sorted.apply(format_display, axis=1)


##########Sidebar formatting############

# Generate a list of options for the multiselect widget
crypto_options = ['All'] + comparison_df_sorted['symbol'].unique().tolist()

# Use st.sidebar.multiselect to create the selection menu
selected_cryptos = st.sidebar.multiselect('Select Cryptocurrencies', options=crypto_options, default=['All'])

# Filter the DataFrame based on the user's selections
if 'All' not in selected_cryptos:
    filtered_df = comparison_df_sorted[comparison_df_sorted['symbol'].isin(selected_cryptos)]
else:
    filtered_df = comparison_df_sorted

# radio buttons for sorting order
sort_order = st.sidebar.radio("Sort Order by % change", ["Ascending", "Descending"])

# sorting based on user selection
if sort_order == "Ascending":
    filtered_df = filtered_df.sort_values(by="percentage_change", ascending=True)
else:
    filtered_df = filtered_df.sort_values(by="percentage_change", ascending=False)

##########Main Page############
with st.sidebar:
    # Display a title for the sidebar section
    st.markdown("""
    <style>
        .scrollbar-div-sidebar {
            height: 400px; /* Adjust height as needed */
            overflow-y: scroll;
            margin-top: 0px; /* Reduce margin above the scrollbar div */
            padding-top: 0px; /* Reduce padding above the scrollbar div */
        }
        .crypto-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }
        .crypto-row .symbol, .crypto-row .current_price, .crypto-row .percentage_change {
            width: 33%;
            text-align: left;
        }
        .crypto-row .current_price, .crypto-row .percentage_change {
            text-align: right;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Apply the format_display function to the filtered DataFrame
    filtered_df['display'] = filtered_df.apply(format_display, axis=1)
    
    if 'display' in filtered_df.columns:
        # Display each item within the div to include in the scrollable area
        for display_text in filtered_df['display']:
            st.markdown(f"<div class='crypto-row'>{display_text}</div>", unsafe_allow_html=True)


##########Set Styling Classes.############

st.markdown("""
<style>
body {
    font-family: 'Arial', sans-serif;
}
            
h1, h2, h3, h4, h5, h6 {
    font-family: 'Helvetica', sans-serif;
            color: lightgrey;
}

p, div, input, textarea {
    font-family: 'Verdana', sans-serif;
}
            
.highlight {
    color: green;
}
</style>
""", unsafe_allow_html=True)




st.markdown("""<div style="text-align: center; " class="title"> <h1> <span class="highlight">C</span>rypto <span class="highlight">P</span>erfomance <span class="highlight">I</span>nsights <br>(<span class="highlight">CPI</span>)</h1> </div>""", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; " class="description">
        This app visualizes data for the top 100 Crypto currencies sorted by marketcap from <a src='https://www.coingecko.com/en/api'>Coin Gecko</a>.
    </div>
    """, unsafe_allow_html=True)

st.divider()



# Show a multiselect widget with the genres using `st.multiselect`.
st.markdown("""<h3>Add and remove Cryptocurrencies to compare and retrieve latest data.</h3>""", unsafe_allow_html=True)
compare_crypto = st.multiselect(
    "Select Cryptocurrencies",
    df.coin_id.unique(),
    default=["bitcoin", "ethereum", "solana"]
)

compare_df = df[df['coin_id'].isin(compare_crypto)]

most_recent_updates = compare_df.groupby('coin_id').apply(lambda x: x.sort_values('last_updated', ascending=False).head(1)).reset_index(drop=True)

selected_cryptos_info = []  

if not most_recent_updates.empty:
    st.write("Selected Cryptocurrencies Most Recent Data:")
    for index, row in most_recent_updates.iterrows():
        crypto_info = {  
            'coin_name': row['name'],
            'price': row['current_price'],
            'market_cap': row['market_cap'],  
            'ticker': row['symbol']
        }
        selected_cryptos_info.append(crypto_info)  

    items_per_row = 0
    
    # Initialize an empty list to hold the current row's columns
    current_row_columns = []
    
    for crypto in selected_cryptos_info:
    # If we've reached 3 items, reset the counter and the current row
        if items_per_row == 3:
            items_per_row = 0
            current_row_columns = []
        
        # If the current row is empty, create a new row of 3 columns
        if items_per_row == 0:
            current_row_columns = st.columns(3)
        
        # Select the appropriate column based on the number of items already in the row
        col = current_row_columns[items_per_row]
        
        html_content = f"""
        <div style="border:2px solid #4CAF50; border-radius: 5px; padding: 10px; margin: 10px;">
            <h4>{crypto['coin_name']}</h4>
            <p>Price: ${crypto['price']}</p>
            <p>Market Cap: ${crypto['market_cap']}</p>
            <p>Ticker: {crypto['ticker']}</p>
        </div>
        """
        
        # Display the crypto information in the selected column with a border
        with col:
            st.markdown(html_content, unsafe_allow_html=True)
        
        # Increment the counter since we've added an item to the current row
        items_per_row += 1

graph_df = df_graph[df_graph['coin_id'].isin(compare_crypto)]

if not graph_df.empty:
    # Create a date range from the minimum to the maximum timestamp in the data
    date_range = pd.date_range(start=graph_df['last_updated'].min(), end=graph_df['last_updated'].max(), freq='H')

    # Reindex the DataFrame to fill missing timestamps
    graph_df = graph_df.set_index('last_updated')
    graph_df = graph_df.groupby('coin_id').apply(lambda group: group.reindex(date_range, method='ffill')).reset_index(level=0, drop=True).reset_index()

    # Remove any remaining duplicates by taking the first entry for each timestamp
    graph_df = graph_df.drop_duplicates(subset=['index', 'coin_id'])

    # Normalize prices within each group of 'coin_id'
    graph_df['normalized_price'] = graph_df.groupby('coin_id')['current_price'].transform(lambda x: (x - x.min()) / (x.max() - x.min()))

    # Pivot the DataFrame to get the format suitable for st.line_chart
    pivot_df = graph_df.pivot(index='index', columns='coin_id', values='normalized_price')
    st.divider()

    st.markdown("""<h3>Normalized Price Data</h3>""", unsafe_allow_html=True)
    # Display the line chart
    st.line_chart(pivot_df)
else:
    # Handle the case when graph_df is empty, e.g., display a message
    st.write("No data available. Please select an option.")

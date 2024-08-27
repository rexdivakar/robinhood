import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objs as go
from scipy.optimize import newton
from datetime import datetime
from plotly.subplots import make_subplots


def get_stock_info(ticker_symbol):
    stock = yf.Ticker(ticker_symbol)
    return stock.info


def fetch_stock_data(ticker_symbol, period="1mo"):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period)
    return hist


def calculate_xirr(cash_flows):
    def npv(rate, cash_flows):
        return sum(
            [
                cf / ((1 + rate) ** ((d - cash_flows[0][0]).days / 365.0))
                for d, cf in cash_flows
            ]
        )

    return newton(lambda r: npv(r, cash_flows), 0.1)


# Set page configuration to widescreen mode
st.set_page_config(layout="wide")

timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
file_name = f"./robinhood_statement_{timestamp}.csv"

# File uploader for CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    with open(file_name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    uploaded_file = file_name


uploaded_file = "./robinhood_statement.csv"

if uploaded_file is not None:
    try:
        # Load the CSV file
        df = pd.read_csv(uploaded_file, encoding="utf-8", on_bad_lines="skip")

        # Filter for "Buy" transactions
        df_buy = df[df["Trans Code"] == "Buy"].copy()

        # Convert relevant columns to numeric and date formats
        df_buy.loc[:, "Activity Date"] = pd.to_datetime(df_buy["Activity Date"]).dt.date
        df_buy.loc[:, "Quantity"] = pd.to_numeric(df_buy["Quantity"], errors="coerce")
        df_buy.loc[:, "Price"] = (
            df_buy["Price"].replace("[\\$,]", "", regex=True).astype(float)
        )

        # Sort by Activity Date
        df_buy = df_buy.sort_values(by="Activity Date")

        # Calculate cumulative quantity over time
        df_buy["Cumulative Quantity"] = df_buy.groupby("Instrument")[
            "Quantity"
        ].cumsum()
        df_buy["Weighted Average Price"] = (
            df_buy.groupby("Instrument")
            .apply(
                lambda x: (x["Price"] * x["Quantity"]).cumsum()
                / x["Cumulative Quantity"]
            )
            .reset_index(drop=True)
        )

        st.success("CSV file loaded successfully!")
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        df_buy = pd.DataFrame()  # Empty DataFrame if there's an error
else:
    st.warning("Please upload a CSV file.")
    df_buy = pd.DataFrame()  # Empty DataFrame if no file is uploaded

st.title("Interactive Stock Analysis")


def display_chart():
    if df_buy.empty:
        st.write("No data available. Please upload a CSV file.")
        return

    # Dropdown to select the stock
    stock_list = df_buy["Instrument"].unique()
    default_stock = "VOO" if "VOO" in stock_list else stock_list[0]
    selected_stock = st.selectbox(
        "Select a Stock to Analyze",
        stock_list,
        index=stock_list.tolist().index(default_stock),
    )

    # Get stock data
    stock_info = get_stock_info(selected_stock)

    # Fetch historical data
    hist_data = fetch_stock_data(selected_stock, period="1mo")

    # Calculate trend
    current_price = hist_data["Close"][-1]
    past_prices = hist_data["Close"].iloc[:-1]  # Exclude the current price
    trend = "Increasing" if current_price > past_prices.mean() else "Decreasing"
    trend_color = "green" if trend == "Increasing" else "red"

    # Filter data for the selected stock
    stock_data = df_buy[df_buy["Instrument"] == selected_stock]
    stock_data["Invested_Amount"] = (
        df_buy["Amount"].replace("[\\$,()]", "", regex=True).astype(float).round(2)
    )

    if not stock_data.empty:
        # Create a subplot with two y-axes
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add trace for cumulative quantity
        fig.add_trace(
            go.Scatter(
                x=stock_data["Activity Date"],
                y=stock_data["Cumulative Quantity"],
                mode="lines+markers",
                name="Cumulative Quantity",
                marker=dict(color="blue"),
                text=[
                    f"Date: {date}<br>Quantity: {qty}"
                    for date, qty in zip(
                        stock_data["Activity Date"], stock_data["Quantity"]
                    )
                ],
                hoverinfo="text",
            ),
            secondary_y=False,
        )

        # Add trace for price
        fig.add_trace(
            go.Scatter(
                x=stock_data["Activity Date"],
                y=stock_data["Price"],
                mode="lines+markers",
                name="Price",
                marker=dict(color="red"),
                text=[
                    f"Date: {date}<br>Price: ${price:.2f}"
                    for date, price in zip(
                        stock_data["Activity Date"], stock_data["Price"]
                    )
                ],
                hoverinfo="text",
            ),
            secondary_y=True,
        )

        # Update layout with titles and axis labels
        fig.update_layout(
            title_text=f"Cumulative Shares and Price for {selected_stock}",
            hovermode="x unified",
        )

        # Format x-axis to show only date
        fig.update_xaxes(
            title_text="Date", tickformat="%Y-%m-%d"  # Ensure only the date is shown
        )

        fig.update_yaxes(title_text="Cumulative Quantity", secondary_y=False)
        fig.update_yaxes(title_text="Price", secondary_y=True)

        # Render the plot in Streamlit
        st.plotly_chart(fig)

        # # Show the raw data in a table
        # st.subheader(f"Raw Data for {selected_stock}")
        # st.write(
        #     stock_data[
        #         ["Activity Date", "Quantity", "Invested_Amount", "Price", "Description"]
        #     ].reset_index(drop=True)
        # )

        # Display stock info
        st.subheader(f"Stock Info: {stock_info.get('longName', 'N/A')}")

        # Display trend
        st.markdown(
            f"<h2 style='color: {trend_color};'>Trend for {stock_info.get('longName')} is : {trend}</h2>",
            unsafe_allow_html=True,
        )

        # Calculate total returns using XIRR
        cash_flows = list(
            zip(stock_data["Activity Date"], -stock_data["Invested_Amount"])
        )
        cash_flows.append(
            (
                datetime.now().date(),
                current_price * stock_data["Cumulative Quantity"].iloc[-1],
            )
        )
        xirr = calculate_xirr(cash_flows)
        total_returns = cash_flows[-1][1] + sum(cf[1] for cf in cash_flows[:-1])
        
        mcol1, mcol2 = st.columns(2)

        # Display XIRR and total returns
        with mcol1:
            st.metric(label="XIRR (Annualized Return)", value=f"{xirr * 100:.2f}%")
        
        with mcol2:
            st.metric(label="Total Return", value=f"${total_returns:.2f}")

        # Create columns
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

        # Display stock info in columns
        with col1:
            st.metric(label="Current Price", value=f"${current_price:.2f}")

        with col2:
            st.metric(
                label="Day High", value=f"${stock_info.get('dayHigh', 'N/A'):.2f}"
            )

        with col3:
            st.metric(label="Day Low", value=f"${stock_info.get('dayLow', 'N/A'):.2f}")

        with col4:
            st.metric(
                label="Regular Market Open",
                value=f"${stock_info.get('regularMarketOpen', 'N/A'):.2f}",
            )

        with col5:
            st.metric(
                label="52-Week High",
                value=f"${stock_info.get('fiftyTwoWeekHigh', 'N/A'):.2f}",
            )

        with col6:
            st.metric(
                label="52-Week Low",
                value=f"${stock_info.get('fiftyTwoWeekLow', 'N/A'):.2f}",
            )

        with col7:
            st.metric(label="PE", value=f"{stock_info.get('trailingPE', 'N/A'):.2f}")

        # Drop down to select the period
        period = st.selectbox(
            "Select the period",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
            index=0,
        )

        # Fetch historical data
        hist_data = fetch_stock_data(selected_stock, period=period)

        # Plot historical data
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=hist_data.index,
                y=hist_data["Close"],
                mode="lines+markers",
                name="Closing Price",
                marker=dict(color="blue"),
            )
        )

        fig.update_layout(
            title_text=f"Price Trend for {selected_stock}",
            xaxis_title="Date",
            yaxis_title="Price",
            hovermode="x unified",
        )

        # Format x-axis to show only date
        fig.update_xaxes(title_text="Date", tickformat="%Y-%m-%d")

        st.plotly_chart(fig)

    else:
        st.write("No data available for the selected stock.")


# Display the chart
display_chart()

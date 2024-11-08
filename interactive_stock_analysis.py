import dash
import pandas as pd
from dash import dcc, html
from dash import dash_table
import plotly.express as px
from pydantic import BaseModel
import dash_bootstrap_components as dbc


class InvestmentData(BaseModel):
    Instrument: str
    Net_Quantity: float
    Average_Price: float
    Total_Invested: float
    Total_Dividends: float


# Function to process data
def process_data():
    # Load the data (update the path to your actual file path)
    df = pd.read_csv("robinhood_statement.csv", encoding="utf-8", on_bad_lines="skip")

    # Filter the transactions for buys, sells, and dividends
    transactions = df[df["Trans Code"].isin(["Buy", "Sell", "CDIV"])].copy()

    # Clean and convert relevant columns to numeric
    transactions["Price"] = (
        transactions["Price"].replace(r"[\$,]", "", regex=True).astype(float)
    )
    transactions["Amount"] = (
        transactions["Amount"].replace(r"[\$,()]", "", regex=True).astype(float)
    )
    transactions["Quantity"] = pd.to_numeric(transactions["Quantity"], errors="coerce")

    # Separate the transactions
    buy_transactions = transactions[transactions["Trans Code"] == "Buy"]
    sell_transactions = transactions[transactions["Trans Code"] == "Sell"]
    dividend_transactions = transactions[transactions["Trans Code"] == "CDIV"]

    # Calculate total cost for each buy transaction
    buy_transactions = buy_transactions.copy()  # Avoid SettingWithCopyWarning
    buy_transactions["Total_Cost"] = (
        buy_transactions["Price"] * buy_transactions["Quantity"]
    )

    # Aggregate buy, sell, and dividend data by instrument
    buy_summary = (
        buy_transactions.groupby("Instrument")
        .agg({"Quantity": "sum", "Total_Cost": "sum"})
        .reset_index()
    )
    sell_summary = (
        sell_transactions.groupby("Instrument")["Quantity"].sum().reset_index()
    )
    dividend_summary = (
        dividend_transactions.groupby("Instrument")["Amount"].sum().reset_index()
    )

    # Merge the buy and sell data
    shares_summary = pd.merge(
        buy_summary,
        sell_summary,
        on="Instrument",
        how="left",
        suffixes=("_buy", "_sell"),
    )
    shares_summary["Quantity_sell"] = shares_summary["Quantity_sell"].fillna(0)

    # Calculate net quantity
    shares_summary["Net_Quantity"] = (
        shares_summary["Quantity_buy"] - shares_summary["Quantity_sell"]
    )

    # Recalculate the total cost for the net quantity
    shares_summary["Adjusted_Cost"] = shares_summary["Total_Cost"] * (
        shares_summary["Net_Quantity"] / shares_summary["Quantity_buy"]
    )

    # Calculate the average price based on the adjusted cost and net quantity
    shares_summary["Average_Price"] = (
        shares_summary["Adjusted_Cost"] / shares_summary["Net_Quantity"]
    ).round(2)

    # Add the total invested column based on the adjusted cost
    shares_summary["Total_Invested"] = shares_summary["Adjusted_Cost"].round(2)

    # Filter out instruments where no shares are currently held
    final_shares = shares_summary[shares_summary["Net_Quantity"] > 0][
        ["Instrument", "Net_Quantity", "Average_Price", "Total_Invested"]
    ]

    # Merge dividend data
    final_summary = pd.merge(
        final_shares, dividend_summary, on="Instrument", how="left"
    )
    final_summary["Total_Dividends"] = final_summary["Amount"].fillna(0)
    final_summary.drop(columns="Amount", inplace=True)

    # Round the final values for clarity
    final_summary["Net_Quantity"] = final_summary["Net_Quantity"].round(3)
    final_summary["Total_Dividends"] = final_summary["Total_Dividends"].round(2)
    final_summary["Total_Invested"] = final_summary["Total_Invested"].round(2)

    return final_summary


# Load the data
df = process_data()

# Calculate additional metrics
df["Dividend_Yield"] = (df["Total_Dividends"] / df["Total_Invested"]) * 100
top_investments = df.sort_values(by="Total_Invested", ascending=False).head(5).round(3)
top_dividend_yield = (
    df.sort_values(by="Dividend_Yield", ascending=False).head(5).round(3)
)

# Summary statistics
total_investment = df["Total_Invested"].sum()
total_dividends = df["Total_Dividends"].sum()
average_dividend_yield = df["Dividend_Yield"].mean()

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SLATE])
app.title = "Comprehensive Investment Dashboard"

# Define the layout of the app
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "Comprehensive Investment Dashboard",
                        className="text-center my-4 text-light",
                    ),
                    width=12,
                )
            ]
        ),
        # Overview Cards
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Total Investment",
                                    className="card-title text-light",
                                ),
                                html.H3(
                                    f"${total_investment:,.2f}",
                                    className="card-text text-success",
                                ),
                            ]
                        ),
                        className="mb-4",
                        color="dark",
                        inverse=True,
                    ),
                    width=4,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Total Dividends", className="card-title text-light"
                                ),
                                html.H3(
                                    f"${total_dividends:,.2f}",
                                    className="card-text text-info",
                                ),
                            ]
                        ),
                        className="mb-4",
                        color="dark",
                        inverse=True,
                    ),
                    width=4,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Average Dividend Yield",
                                    className="card-title text-light",
                                ),
                                html.H3(
                                    f"{average_dividend_yield:.2f}%",
                                    className="card-text text-warning",
                                ),
                            ]
                        ),
                        className="mb-4",
                        color="dark",
                        inverse=True,
                    ),
                    width=4,
                ),
            ]
        ),
        # Tables and Charts
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Top Investments",
                                        className="card-title text-center mb-4 text-light",
                                    ),
                                    dash_table.DataTable(
                                        id="top-investments-table",
                                        columns=[
                                            {"name": col, "id": col}
                                            for col in top_investments.columns
                                        ],
                                        data=top_investments.to_dict("records"),
                                        page_size=5,
                                        style_table={
                                            "height": "300px",
                                            "overflowY": "auto",
                                            "width": "100%",
                                            "border": "1px solid #444",
                                            "boxShadow": "0px 4px 12px rgba(0, 0, 0, 0.3)",
                                            "borderRadius": "10px",
                                        },
                                        style_header={
                                            "backgroundColor": "#1b1b1b",
                                            "fontWeight": "bold",
                                            "color": "#e2e2e2",
                                            "borderBottom": "1px solid #444",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "10px",
                                            "fontSize": "14px",
                                            "border": "1px solid #444",
                                            "backgroundColor": "#2a2a2a",
                                            "color": "#e2e2e2",
                                        },
                                    ),
                                ]
                            ),
                            style={
                                "height": "100%",
                                "backgroundColor": "#222",
                                "borderRadius": "12px",
                            },
                        )
                    ],
                    width=6,
                    className="mb-4",
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Top Dividend Yield Instruments",
                                        className="card-title text-center mb-4 text-light",
                                    ),
                                    dash_table.DataTable(
                                        id="top-dividend-yield-table",
                                        columns=[
                                            {"name": col, "id": col}
                                            for col in top_dividend_yield.columns
                                        ],
                                        data=top_dividend_yield.to_dict("records"),
                                        page_size=5,
                                        style_table={
                                            "height": "300px",
                                            "overflowY": "auto",
                                            "width": "100%",
                                            "border": "1px solid #444",
                                            "boxShadow": "0px 4px 12px rgba(0, 0, 0, 0.3)",
                                            "borderRadius": "10px",
                                        },
                                        style_header={
                                            "backgroundColor": "#1b1b1b",
                                            "fontWeight": "bold",
                                            "color": "#e2e2e2",
                                            "borderBottom": "1px solid #444",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "10px",
                                            "fontSize": "14px",
                                            "border": "1px solid #444",
                                            "backgroundColor": "#2a2a2a",
                                            "color": "#e2e2e2",
                                        },
                                    ),
                                ]
                            ),
                            style={
                                "height": "100%",
                                "backgroundColor": "#222",
                                "borderRadius": "12px",
                            },
                        )
                    ],
                    width=6,
                    className="mb-4",
                ),
            ]
        ),
        # Charts
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Investment Distribution",
                                        className="card-title text-center mb-4 text-light",
                                    ),
                                    dcc.Graph(
                                        id="pie-chart",
                                        figure=px.pie(
                                            df,
                                            names="Instrument",
                                            values="Total_Invested",
                                            title="Portfolio Distribution",
                                            hole=0.4,
                                            template="plotly_dark",
                                            color_discrete_sequence=px.colors.sequential.Plasma,
                                        ).update_layout(
                                            showlegend=True,
                                            title_x=0.5,
                                            margin=dict(l=20, r=20, t=40, b=20),
                                            transition={
                                                "duration": 800,
                                                "easing": "cubic-in-out",
                                            },
                                        ),
                                    ),
                                ]
                            ),
                            style={"backgroundColor": "#222", "borderRadius": "12px"},
                        )
                    ],
                    width=6,
                    className="mb-4",
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Top Investments (Bar Chart)",
                                        className="card-title text-center mb-4 text-light",
                                    ),
                                    dcc.Graph(
                                        id="bar-chart",
                                        figure=px.bar(
                                            top_investments,
                                            x="Instrument",
                                            y="Total_Invested",
                                            title="Top Investments by Total Invested Amount",
                                            labels={
                                                "Total_Invested": "Total Invested ($)",
                                                "Instrument": "Stock",
                                            },
                                            template="plotly_dark",
                                        ).update_layout(
                                            margin=dict(l=20, r=20, t=40, b=20),
                                            transition={
                                                "duration": 800,
                                                "easing": "cubic-in-out",
                                            },
                                        ),
                                    ),
                                ]
                            ),
                            style={"backgroundColor": "#222", "borderRadius": "12px"},
                        )
                    ],
                    width=6,
                    className="mb-4",
                ),
            ]
        ),
        # Final Summary Table
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H4(
                                        "Final Investment Summary",
                                        className="card-title text-center mb-4 text-light",
                                    ),
                                    dash_table.DataTable(
                                        id="final-summary-table",
                                        columns=[
                                            {"name": col, "id": col}
                                            for col in df.columns
                                        ],
                                        data=df.to_dict("records"),
                                        page_size=10,
                                        style_table={
                                            "height": "400px",
                                            "overflowY": "auto",
                                            "width": "100%",
                                            "border": "1px solid #444",
                                            "boxShadow": "0px 4px 12px rgba(0, 0, 0, 0.3)",
                                            "borderRadius": "10px",
                                        },
                                        style_header={
                                            "backgroundColor": "#1b1b1b",
                                            "fontWeight": "bold",
                                            "color": "#e2e2e2",
                                            "borderBottom": "1px solid #444",
                                        },
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "10px",
                                            "fontSize": "14px",
                                            "border": "1px solid #444",
                                            "backgroundColor": "#2a2a2a",
                                            "color": "#e2e2e2",
                                        },
                                    ),
                                ]
                            ),
                            style={
                                "backgroundColor": "#222",
                                "borderRadius": "12px",
                            },
                        )
                    ],
                    width=12,
                    className="mb-4",
                ),
            ]
        ),
    ],
    fluid=True,
    style={"backgroundColor": "#1a1a1a", "padding": "20px"},
)

# Run the app
if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)

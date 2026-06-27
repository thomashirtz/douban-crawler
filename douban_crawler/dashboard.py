from pathlib import Path

import dash
import pandas as pd
from dash import Input, Output, dash_table, dcc, html

from douban_crawler import default

DATA_PATH = Path(default.OUTPUT_PATH)
app = dash.Dash(__name__)


def _build_layout():
    if not DATA_PATH.exists():
        return html.Div(
            [
                html.H3("No data yet"),
                html.P("Run: dc crawl"),
                html.P(f"Expected file: {DATA_PATH}"),
            ],
            style={"padding": "2rem"},
        )

    df = pd.read_json(DATA_PATH, lines=True)
    df["release_date"] = pd.to_datetime(df["initial_release_date"], errors="coerce", format="mixed")
    df["rating_people_num"] = pd.to_numeric(df["rating_people"], errors="coerce")

    all_genres = sorted({g for genres in df["genres"] if isinstance(genres, list) for g in genres})
    countries = sorted(df["production_countries_regions"].dropna().unique())
    min_date = df["release_date"].min()
    max_date = df["release_date"].max()
    date_min = min_date.strftime("%Y-%m-%d") if pd.notna(min_date) else None
    date_max = max_date.strftime("%Y-%m-%d") if pd.notna(max_date) else None

    layout = html.Div(
        [
            html.H2("Douban Movies"),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Date range"),
                            dcc.DatePickerRange(
                                id="date-range",
                                start_date=date_min,
                                end_date=date_max,
                                display_format="YYYY-MM-DD",
                            ),
                            html.Label("Country"),
                            dcc.Dropdown(
                                id="country",
                                options=[{"label": c, "value": c} for c in countries],
                                multi=True,
                                placeholder="All countries",
                            ),
                            html.Label("Genre"),
                            dcc.Dropdown(
                                id="genre",
                                options=[{"label": g, "value": g} for g in all_genres],
                                multi=True,
                                placeholder="All genres",
                            ),
                            html.Label("Min rating"),
                            dcc.Slider(
                                id="min-rate",
                                min=0,
                                max=10,
                                step=0.5,
                                value=0,
                                marks={i: str(i) for i in range(11)},
                            ),
                            html.Label("Sort by"),
                            dcc.Dropdown(
                                id="sort-by",
                                options=[
                                    {"label": "Rating (high first)", "value": "rate"},
                                    {"label": "Release date (new first)", "value": "release_date"},
                                    {"label": "Rating count (high first)", "value": "rating_people_num"},
                                ],
                                value="rate",
                            ),
                        ],
                        style={"width": "220px", "padding": "1rem", "borderRight": "1px solid #ddd"},
                    ),
                    html.Div(
                        [
                            html.P(id="row-count"),
                            dash_table.DataTable(
                                id="table",
                                page_size=20,
                                sort_action="native",
                                filter_action="native",
                                style_table={"overflowX": "auto"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "8px",
                                    "maxWidth": "300px",
                                    "overflow": "hidden",
                                },
                                style_header={"fontWeight": "bold"},
                            ),
                        ],
                        style={"flex": 1, "padding": "1rem"},
                    ),
                ],
                style={"display": "flex"},
            ),
        ]
    )

    @app.callback(
        Output("table", "data"),
        Output("table", "columns"),
        Output("row-count", "children"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("country", "value"),
        Input("genre", "value"),
        Input("min-rate", "value"),
        Input("sort-by", "value"),
    )
    def update_table(start_date, end_date, countries_sel, genres_sel, min_rate, sort_by):
        filtered = df.copy()
        if start_date:
            filtered = filtered[filtered["release_date"] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered["release_date"] <= pd.to_datetime(end_date)]
        if countries_sel:
            mask = filtered["production_countries_regions"].apply(
                lambda c: any(country in str(c) for country in countries_sel)
            )
            filtered = filtered[mask]
        if genres_sel:
            filtered = filtered[
                filtered["genres"].apply(
                    lambda gs: isinstance(gs, list) and any(g in gs for g in genres_sel)
                )
            ]
        if min_rate:
            filtered = filtered[filtered["rate"].fillna(0) >= min_rate]
        if sort_by == "release_date":
            filtered = filtered.sort_values("release_date", ascending=False, na_position="last")
        elif sort_by == "rating_people_num":
            filtered = filtered.sort_values("rating_people_num", ascending=False, na_position="last")
        else:
            filtered = filtered.sort_values("rate", ascending=False, na_position="last")

        display_cols = [
            "title",
            "rate",
            "rating_people",
            "initial_release_date",
            "production_countries_regions",
            "genres",
            "directors",
            "actors",
            "url",
        ]
        show = filtered[display_cols].copy()
        for col in ("genres", "directors", "actors"):
            show[col] = show[col].apply(lambda v: ", ".join(v) if isinstance(v, list) else v)

        columns = [{"name": c, "id": c, "presentation": "markdown" if c == "url" else "input"} for c in display_cols]
        data = show.to_dict("records")
        for row in data:
            if row.get("url"):
                row["url"] = f"[link]({row['url']})"

        return data, columns, f"{len(filtered)} movies"

    return layout


app.layout = _build_layout()


def run(debug: bool = True, port: int = 8050):
    app.run(debug=debug, port=port)

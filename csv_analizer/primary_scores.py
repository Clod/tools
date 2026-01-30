import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import os
    return mo, pd


@app.cell
def _(mo):
    mo.md(r"""
    # Primary Safety Scores Analyzer
    This notebook displays the contents of `primary_safety_scores_transports.csv`.
    """)
    return


@app.cell
def _(mo, pd):
    csv_path = "/Users/claudiograsso/Documents/Sentiance/tools/csv/primary_safety_scores_transports.csv"

    if pd.io.common.file_exists(csv_path):
        df = pd.read_csv(csv_path)
        # Handle -1.0 as NaN for stats if they represent missing data, 
        # but let's keep them as is for now unless confirmed.
        table = mo.ui.table(df, label="Safety Scores Grid", selection=None, pagination=True)

        # Summary stats
        stats = df.describe().reset_index()
        stats_table = mo.ui.table(stats, label="Summary Statistics")
    else:
        df = None
        table = mo.callout(f"File not found: {csv_path}", kind="danger")
        stats_table = None
        stats = None # Added to match the return statement

    return stats_table, table


@app.cell
def _(mo, stats_table, table):
    mo.vstack([
        mo.md("## Safety Scores Grid"),
        table,
        mo.md("## Summary Statistics"),
        stats_table
    ]) if table and stats_table else table
    return


if __name__ == "__main__":
    app.run()

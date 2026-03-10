import marimo
__generated_with = "0.19.6"
app = marimo.App()

@app.cell
def _():
    import marimo as mo
    return mo,

@app.cell
def _(mo):
    mo.md("Hello World")
    return

if __name__ == "__main__":
    app.run()

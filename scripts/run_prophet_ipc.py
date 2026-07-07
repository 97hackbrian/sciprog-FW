#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import sys
from pathlib import Path

# ensure libs/ is on the path
_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir.parent / "libs"))

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from prophet import Prophet
from prophet.plot import add_changepoints_to_plot

from benchmarking import benchmark
from logger import configure_logging

sns.set_theme()


def _title(ax: plt.Axes, text: str) -> None:
    ax.set_title(text, fontsize=13, fontweight='bold')


def main() -> None:
    # read the data
    df = pd.read_csv(root_dir / 'data' / 'ipc.csv', parse_dates=['ds'])
    log.debug(f"head:\n{df.head()}")
    log.debug(f"data range: {df['ds'].min()} to {df['ds'].max()}")
    log.debug(f"rows: {len(df)}")

    # build the model
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10,
    )

    # fit
    with benchmark("train model", log):
        model.fit(df)

    # changepoints
    log.debug(f"changepoints:\n{pd.DataFrame({'ds': model.changepoints})}")

    # --- forecast: 6 months (180 days) ---
    future = model.make_future_dataframe(periods=6, freq='MS')
    forecast = model.predict(future)

    preds = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    log.debug(f"forecast tail (next 6 months):\n{preds.tail(6).to_string(index=False)}")
    log.info(f"forecast (last 6 months):\n{preds.tail(6).to_string(index=False)}")

    # --- 1. Forecast plot with changepoints ---
    fig1 = model.plot(forecast)
    _title(fig1.gca(), 'Proyecci\u00f3n IPC mensual — 6 meses')
    fig1.gca().set_xlabel('Fecha')
    fig1.gca().set_ylabel('Variaci\u00f3n mensual IPC (%)')
    add_changepoints_to_plot(fig1.gca(), model, forecast)
    fig1.tight_layout()
    plt.show()
    plt.close(fig1)

    # --- 2. Components plot ---
    fig2 = model.plot_components(forecast)
    for ax, t in zip(fig2.axes, ['Tendencia', 'Estacionalidad anual']):
        _title(ax, t)
    fig2.tight_layout()
    plt.show()
    plt.close(fig2)


if __name__ == '__main__':
    configure_logging(logging.DEBUG)
    log = logging.getLogger(__name__)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")

#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import sys
from pathlib import Path

# ensure libs/ is on the path
_script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_script_dir.parent / "libs"))

import pandas as pd
from matplotlib import pyplot as plt
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
from prophet.plot import add_changepoints_to_plot

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]


def main() -> None:
    # get the data to analyze
    df = pd.read_csv(
        'https://raw.githubusercontent.com/facebook/prophet/main/examples/example_wp_log_peyton_manning.csv')
    log.debug(f"head:\n{df.head()}")

    # build the default model
    model = Prophet()
    with benchmark("train model", log):
        model.fit(df)

    # create one year in the future
    future = model.make_future_dataframe(periods=365)
    forecast = model.predict(future)
    log.debug(f"predict tail:\n{forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()}")

    # forecast with changepoints
    fig1 = model.plot(forecast)

    # add change points to the graph
    add_changepoints_to_plot(fig1.gca(), model, forecast)

    # show where are the change points
    log.debug(f"changepoints:\n{pd.DataFrame({'ds': model.changepoints})}")
    plt.show()
    plt.close(fig1)

    # show the components
    fig2 = model.plot_components(forecast)
    plt.show()
    plt.close(fig2)

    # cross-validation
    with benchmark("cross-validation", log):
        df_cv = cross_validation(model, initial='730 days', period='180 days', horizon='365 days')
    df_metrics = performance_metrics(df_cv)
    log.info(f"CV metrics:\n{df_metrics[['horizon', 'rmse', 'mae', 'mape']].to_string(index=False)}")

    # cross-validation graph
    fig4, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df_cv['y'], df_cv['yhat'], s=5, alpha=0.3)
    lims = [
        min(df_cv['y'].min(), df_cv['yhat'].min()),
        max(df_cv['y'].max(), df_cv['yhat'].max()),
    ]
    ax.plot(lims, lims, 'r--', linewidth=1, label='perfect fit')
    ax.set_xlabel('actual')
    ax.set_ylabel('predicted')
    ax.set_title('Cross-Validation: Actual vs Predicted')
    ax.grid(True)
    ax.legend()
    ax.set_aspect('equal')
    fig4.tight_layout()
    plt.show()
    plt.close(fig4)


# call the main function
if __name__ == '__main__':
    configure_logging(logging.DEBUG)
    log = logging.getLogger(__name__)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("starting ..")
        main()
        log.info("done.")

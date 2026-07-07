#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import pickle
from pathlib import Path

import pandas as pd
import streamlit
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from sklearn.ensemble import RandomForestClassifier

from benchmarking import benchmark
from logger import configure_logging


@streamlit.cache_resource(show_spinner=True)
def load_iris_model(model_path: Path) -> RandomForestClassifier:
    log.info(f"Loading iris random forest model from {model_path} ..")
    if not model_path.exists():
        raise FileNotFoundError(
            f"Can't find the model at {model_path}, aborted!"
        )

    with model_path.open("rb") as f:
        return pickle.load(f)


def plot_probabilities(probabilities_df: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    probabilities_df.plot(kind="bar", legend=False, ax=ax, color="#4C78A8")
    ax.set_title("Prediction probabilities")
    ax.set_ylabel("Probability")
    ax.set_xlabel("Species")
    ax.set_ylim(0.0, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def main() -> None:
    # page title
    streamlit.set_page_config(page_title="Iris Flower Species Prediction", page_icon="🌸")

    # load the model
    try:
        rfc = load_iris_model(output_dir / "iris_rf.pkl")
    except Exception as e:
        streamlit.error(f"Error loading the model: {e}")
        streamlit.stop()

    # titles
    streamlit.title("Iris Flower Species Prediction")
    streamlit.markdown(
        "Pre-trained **Random Forest model** to predict the species of Iris flower. "
    )
    streamlit.caption("Adjust the flower measurements and click **Predict species**.")

    # form
    with streamlit.form("iris_prediction_form"):
        streamlit.header("Iris Features")
        col_one, col_two = streamlit.columns(2)

        with col_one:
            streamlit.text("Sepal Characteristics")
            sepal_lenght = streamlit.slider(
                "Select Sepal Length",
                4.0,
                8.0,
                6.0,
                0.2,
            )
            sepal_width = streamlit.slider(
                "Select Sepal Width",
                2.0,
                5.0,
                3.0,
                0.2,
            )

        with col_two:
            streamlit.text("Petal Characteristics")
            petal_length = streamlit.slider(
                "Select Petal Length",
                1.0,
                7.0,
                1.5,
                0.2,
            )
            petal_width = streamlit.slider(
                "Select Petal Width",
                0.1,
                3.0,
                1.0,
                0.2,
            )

        submitted = streamlit.form_submit_button("Predict Species")

    if not submitted:
        streamlit.info("Select the flower measurements, then click **Predict species**.")
        return

    # build a dataframe from the values
    values = pd.DataFrame(
        data=[[sepal_lenght, sepal_width, petal_length, petal_width]],
        # warning: need to be the same names of the model
        columns=["sepal length", "sepal width", "petal length", "petal width"]
    )

    # predict the value
    prediction = rfc.predict(values)[0]
    probabilities = rfc.predict_proba(values)[0]

    # build a dataframe with the probabilities
    probabilities_df = (
        pd.DataFrame({"Species": rfc.classes_, "Probability": probabilities})
        .set_index("Species")
        .sort_values("Probability", ascending=False)
    )

    # show the prediction
    streamlit.success(f"Iris Flower Prediction: **{prediction}**.")

    # show the dataframe as table
    streamlit.dataframe(
        probabilities_df.style.format({"Probability": "{:.2%}"}),
        width='stretch',
    )

    # display the probabilities as a bar chart
    probabilities_df = pd.DataFrame(
        data=probabilities,
        index=rfc.classes_,
        columns=["Probability"]
    )

    # the graphics
    fig = plot_probabilities(probabilities_df)
    streamlit.pyplot(fig)
    plt.close(fig)


# call the main function
if __name__ == '__main__':
    # configure the logging
    configure_logging(logging.DEBUG)
    # get the main logger
    log = logging.getLogger(__name__)

    # get the root directory
    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    # get the output directory
    output_dir = root_dir / "output"
    log.debug(f"output_dir: {output_dir}")

    # measure time
    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")

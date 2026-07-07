#  Copyright (c) 2026. Programacion Cientifica, DISC, Antofagasta, Chile.
import logging
import pickle
from pathlib import Path

from matplotlib import pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.tree import plot_tree
from ucimlrepo import fetch_ucirepo

from benchmarking import benchmark
from logger import configure_logging


def visualize_random_forest(model: RandomForestClassifier, X):
    fig, ax = plt.subplots(figsize=(10, 10))
    plot_tree(
        model.estimators_[0],
        feature_names=X.columns.tolist(),
        class_names=[str(class_name) for class_name in model.classes_],
        filled=True,
        rounded=True,
        fontsize=10,
        ax=ax,
    )
    fig.tight_layout()
    plt.show()
    plt.close(fig)


def main():
    # retrieve the dataset
    iris = fetch_ucirepo(id=53)
    log.debug(f"iris:\n{iris}")

    # data (as pandas dataframes)
    X = iris.data.features
    y = iris.data.targets.squeeze("columns")

    # divide the dataset in train and test (20%)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,  #
    )
    log.debug(f"X_train: {len(X_train)}, X_test: {len(X_test)}, y_train: {len(y_train)}, y_test: {len(y_test)}")

    # training the classifier
    rfc = RandomForestClassifier(random_state=42, max_depth=2)
    with benchmark("training random forest", log):
        log.debug("Training ..")
        rfc.fit(X_train, y_train)

    # testing the model
    y_pred = rfc.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    log.debug(f"accuracy: {accuracy:.2f}")

    # save the model in pickle!
    with open(output_dir / "iris_rf.pkl", "wb") as f:
        pickle.dump(rfc, f)

    # visualize the model
    visualize_random_forest(rfc, X)


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

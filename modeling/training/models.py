from __future__ import annotations

from typing import Any

from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression

from modeling.app.config import Settings


def build_model(settings: Settings) -> Any:
    model_type = settings.model_type
    task_type = settings.task_type

    if model_type == "logistic_regression":
        if task_type != "classification":
            raise ValueError("MODEL_TYPE=logistic_regression only supports TASK_TYPE=classification")
        return LogisticRegression(max_iter=2000, random_state=settings.train_test_seed)

    if model_type == "random_forest":
        if task_type == "classification":
            return RandomForestClassifier(
                n_estimators=300,
                max_depth=None,
                min_samples_leaf=2,
                random_state=settings.train_test_seed,
                n_jobs=-1,
            )
        return RandomForestRegressor(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=2,
            random_state=settings.train_test_seed,
            n_jobs=-1,
        )

    if model_type == "gradient_boosting":
        if task_type == "classification":
            return HistGradientBoostingClassifier(random_state=settings.train_test_seed)
        return HistGradientBoostingRegressor(random_state=settings.train_test_seed)

    if model_type == "xgboost":
        if not settings.enable_xgboost:
            raise ValueError("MODEL_TYPE=xgboost requires ENABLE_XGBOOST=true")

        try:
            from xgboost import XGBClassifier, XGBRegressor
        except ImportError as exc:
            raise RuntimeError("xgboost is not installed. Install extra dependency: pip install -e '.[xgboost]'") from exc

        if task_type == "classification":
            return XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                random_state=settings.train_test_seed,
                eval_metric="logloss",
            )

        return XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=settings.train_test_seed,
        )

    raise ValueError(f"Unsupported model type: {model_type}")


def extract_model_hyperparameters(model: Any) -> dict[str, Any]:
    if hasattr(model, "get_params"):
        params = model.get_params(deep=False)
        return {str(k): v for k, v in params.items()}
    return {"model_repr": repr(model)}

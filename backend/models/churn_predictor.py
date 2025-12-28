"""
User Churn Prediction Model
ML-powered predictive analytics for user retention
"""

import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)

logger = logging.getLogger(__name__)


class ChurnPredictor:
    """
    Machine Learning model for predicting user churn probability.

    Features:
    - days_since_signup: Days since user registration
    - login_count: Total number of logins
    - feature_usage_score: Weighted score of feature interactions
    - plan_tier: Subscription plan level (0=trial, 1=starter, 2=pro, 3=enterprise)
    - last_login_days_ago: Days since last login
    - session_duration_avg: Average session duration (minutes)
    - api_calls_30d: API calls in last 30 days

    Model: Logistic Regression
    Training: Last 6 months of user behavior data
    Retraining: Weekly scheduled task
    """

    FEATURE_COLUMNS = [
        "days_since_signup",
        "login_count",
        "feature_usage_score",
        "plan_tier",
        "last_login_days_ago",
        "session_duration_avg",
        "api_calls_30d",
    ]

    PLAN_TIER_MAP = {"trial": 0, "starter": 1, "professional": 2, "enterprise": 3}

    CHURN_THRESHOLD_DAYS = 30  # User inactive for 30+ days = churned

    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize churn predictor.

        Args:
            model_path: Path to saved model pickle file
        """
        self.model = LogisticRegression(
            max_iter=1000, random_state=42, class_weight="balanced"
        )
        self.scaler = StandardScaler()
        self.model_path = (
            model_path
            or Path(__file__).parent.parent / "data" / "churn_model.pkl"
        )
        self.scaler_path = (
            model_path.parent / "churn_scaler.pkl" if model_path else
            Path(__file__).parent.parent / "data" / "churn_scaler.pkl"
        )
        self.trained = False
        self.training_date = None
        self.feature_importance = None

        # Create data directory if not exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

    def prepare_features(
        self, users_data: List[Dict], for_training: bool = False
    ) -> pd.DataFrame:
        """
        Prepare user features for ML model.

        Args:
            users_data: List of user dictionaries with raw data
            for_training: If True, include churn label

        Returns:
            DataFrame with engineered features
        """
        df = pd.DataFrame(users_data)

        # Calculate days since signup
        if "created_at" in df.columns:
            df["days_since_signup"] = (
                datetime.now() - pd.to_datetime(df["created_at"])
            ).dt.days
        else:
            df["days_since_signup"] = 0

        # Calculate days since last login
        if "last_login" in df.columns:
            df["last_login_days_ago"] = (
                datetime.now() - pd.to_datetime(df["last_login"])
            ).dt.days
            df["last_login_days_ago"] = df["last_login_days_ago"].fillna(999)
        else:
            df["last_login_days_ago"] = 999

        # Login count (default to 0)
        if "login_count" not in df.columns:
            df["login_count"] = 0

        # Feature usage score (weighted sum of interactions)
        # Default to 0 if not provided
        if "feature_usage_score" not in df.columns:
            df["feature_usage_score"] = 0

        # Convert plan tier to numeric
        if "plan_tier" in df.columns:
            df["plan_tier"] = df["plan_tier"].map(self.PLAN_TIER_MAP).fillna(0)
        else:
            df["plan_tier"] = 0

        # Session duration average (minutes)
        if "session_duration_avg" not in df.columns:
            df["session_duration_avg"] = 0

        # API calls in last 30 days
        if "api_calls_30d" not in df.columns:
            df["api_calls_30d"] = 0

        # For training, create churn label
        if for_training:
            df["churned"] = (df["last_login_days_ago"] >= self.CHURN_THRESHOLD_DAYS).astype(
                int
            )

        # Select only feature columns
        feature_df = df[self.FEATURE_COLUMNS].copy()

        # Fill any remaining NaN values
        feature_df = feature_df.fillna(0)

        return feature_df

    def train(
        self,
        users_data: List[Dict],
        test_size: float = 0.2,
        cv_folds: int = 5,
    ) -> Dict[str, any]:
        """
        Train churn prediction model on historical data.

        Args:
            users_data: List of user dictionaries with historical behavior
            test_size: Fraction of data for testing
            cv_folds: Number of cross-validation folds

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training churn model with {len(users_data)} users")

        # Prepare features
        df = self.prepare_features(users_data, for_training=True)
        X = df[self.FEATURE_COLUMNS]
        y = df["churned"]

        # Check class distribution
        churn_rate = y.mean()
        logger.info(f"Churn rate in training data: {churn_rate:.2%}")

        if churn_rate == 0 or churn_rate == 1:
            logger.warning("Training data has only one class! Model may not generalize well.")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.trained = True
        self.training_date = datetime.now()

        # Calculate feature importance (coefficient magnitudes)
        self.feature_importance = dict(
            zip(
                self.FEATURE_COLUMNS,
                np.abs(self.model.coef_[0]).tolist(),
            )
        )

        # Evaluate model
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)

        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=cv_folds, scoring="roc_auc"
        )

        # Predictions
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        # Metrics
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
        except ValueError:
            roc_auc = 0.0
            logger.warning("Could not calculate ROC AUC - only one class present")

        conf_matrix = confusion_matrix(y_test, y_pred).tolist()
        class_report = classification_report(y_test, y_pred, output_dict=True)

        metrics = {
            "train_accuracy": float(train_score),
            "test_accuracy": float(test_score),
            "cv_mean_roc_auc": float(cv_scores.mean()),
            "cv_std_roc_auc": float(cv_scores.std()),
            "test_roc_auc": float(roc_auc),
            "confusion_matrix": conf_matrix,
            "classification_report": class_report,
            "feature_importance": self.feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "churn_rate": float(churn_rate),
            "training_date": self.training_date.isoformat(),
        }

        logger.info(f"Model training complete. Test accuracy: {test_score:.3f}, ROC AUC: {roc_auc:.3f}")

        return metrics

    def predict(self, users_data: List[Dict]) -> List[Dict]:
        """
        Predict churn probability for users.

        Args:
            users_data: List of user dictionaries

        Returns:
            List of predictions with user_id, churn_probability, risk_level
        """
        if not self.trained:
            logger.warning("Model not trained yet. Attempting to load from disk.")
            if not self.load_model():
                logger.error("No trained model available. Returning default predictions.")
                return [
                    {
                        "user_id": user.get("user_id", "unknown"),
                        "username": user.get("username", "unknown"),
                        "churn_probability": 50.0,
                        "risk_level": "medium",
                        "error": "Model not trained",
                    }
                    for user in users_data
                ]

        # Prepare features
        X = self.prepare_features(users_data, for_training=False)
        X_scaled = self.scaler.transform(X)

        # Predict probabilities
        probabilities = self.model.predict_proba(X_scaled)[:, 1]

        # Build predictions
        predictions = []
        for i, user in enumerate(users_data):
            prob = float(probabilities[i]) * 100  # Convert to percentage

            # Determine risk level
            if prob >= 70:
                risk_level = "high"
            elif prob >= 40:
                risk_level = "medium"
            else:
                risk_level = "low"

            predictions.append(
                {
                    "user_id": user.get("user_id", f"user_{i}"),
                    "username": user.get("username", "unknown"),
                    "churn_probability": round(prob, 2),
                    "risk_level": risk_level,
                    "days_since_signup": int(X.iloc[i]["days_since_signup"]),
                    "last_login_days_ago": int(X.iloc[i]["last_login_days_ago"]),
                    "login_count": int(X.iloc[i]["login_count"]),
                }
            )

        return predictions

    def save_model(self) -> bool:
        """
        Persist trained model and scaler to disk.

        Returns:
            True if successful, False otherwise
        """
        if not self.trained:
            logger.error("Cannot save untrained model")
            return False

        try:
            # Save model
            with open(self.model_path, "wb") as f:
                pickle.dump(
                    {
                        "model": self.model,
                        "training_date": self.training_date,
                        "feature_importance": self.feature_importance,
                    },
                    f,
                )

            # Save scaler
            with open(self.scaler_path, "wb") as f:
                pickle.dump(self.scaler, f)

            logger.info(f"Model saved to {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load_model(self) -> bool:
        """
        Load pre-trained model and scaler from disk.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load model
            if not self.model_path.exists():
                logger.warning(f"Model file not found: {self.model_path}")
                return False

            with open(self.model_path, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.training_date = data.get("training_date")
                self.feature_importance = data.get("feature_importance")

            # Load scaler
            if not self.scaler_path.exists():
                logger.warning(f"Scaler file not found: {self.scaler_path}")
                return False

            with open(self.scaler_path, "rb") as f:
                self.scaler = pickle.load(f)

            self.trained = True
            logger.info(f"Model loaded from {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def get_model_info(self) -> Dict:
        """
        Get information about the current model.

        Returns:
            Dictionary with model metadata
        """
        return {
            "trained": self.trained,
            "training_date": self.training_date.isoformat() if self.training_date else None,
            "feature_importance": self.feature_importance,
            "feature_columns": self.FEATURE_COLUMNS,
            "model_type": "Logistic Regression",
            "churn_threshold_days": self.CHURN_THRESHOLD_DAYS,
        }

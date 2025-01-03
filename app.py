import os
import subprocess


required_packages = ['openpyxl', 'lime', 'shap']

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call(['pip', 'install', package])

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression, LinearRegression
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, brier_score_loss, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler, LabelEncoder
import shap
from sklearn.utils import resample
import lime
import lime.lime_tabular
from io import BytesIO

# Styling Properties and Theme
st.set_page_config(page_title="Data Analysis Tool", page_icon="🧠", layout="wide")
st.markdown("<style>body {background-color: #ffffff;}</style>", unsafe_allow_html=True)

# Application Title and Descriptions
st.title("🔍 Explainable Data Analysis Tool")
st.markdown(
    """
    **Welcome to the Data Analysis Tool!** 👋  
    Upload your dataset, visualize with t-SNE and PCA, train the model, and explain predictions using XAI.  
    This tool is designed to make machine learning more accessible and explainable in biomedical research.
    """
)

# Web Site Name
st.sidebar.header("🌐 Web Site: Explainable Data Analysis for Biomedical Application ")

# File Upload by User
st.sidebar.header("🗂 Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Upload your data (Excel or CSV format)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file, sep=None, engine='python')  # Load CSV with auto delimiter detection
    else:
        
        data = pd.read_excel(uploaded_file, engine='openpyxl')
    data = data.dropna()  # Drop any missing values
    st.sidebar.success("Data successfully loaded!")
    st.write("### 📊 Uploaded Data Preview")
    st.dataframe(data.head())

    # Automatic Detection of Target and Features based on data types
    numeric_columns = data.select_dtypes(include=np.number).columns.tolist()
    categorical_columns = data.select_dtypes(include='object').columns.tolist()

    # Allow user to select model type manually
    model_type = st.sidebar.radio("Select Model Type", ["Classification", "Regression"], help="Choose whether to perform classification or regression.")

    if model_type == "Classification":
        # If there are categorical columns, assume classification
        target_column = st.selectbox("Select the target column for model training", categorical_columns + numeric_columns, help="This column will be used as the target variable for classification.")
        feature_columns = [col for col in data.columns if col != target_column]
    elif model_type == "Regression":
        # If all columns are numeric, assume regression
        target_column = st.selectbox("Select the target column for model training", numeric_columns, help="This column will be used as the target variable for regression.")
        feature_columns = [col for col in data.columns if col != target_column]
    else:
        st.error("No suitable columns found for modeling. Please upload a dataset with appropriate target and feature columns.")
        st.stop()

    if target_column and feature_columns:
        X = data[feature_columns].values
        y = data[target_column].values

        # Determine if target column is continuous or categorical
        if model_type == "Classification":
            y = LabelEncoder().fit_transform(y)

        # Split data into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Standardize data
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # t-SNE Analysis
        st.write("### 🌀 t-SNE Analysis")
        if st.button("Run t-SNE Analysis"):
            try:
                tsne = TSNE(n_components=2, random_state=42)
                tsne_results = tsne.fit_transform(X)
                st.write("#### t-SNE Results Visualization")
                tsne_df = pd.DataFrame(tsne_results, columns=['t-SNE Dimension 1', 't-SNE Dimension 2'])
                tsne_df[target_column] = y
                plt.figure(figsize=(10, 6))
                sns.scatterplot(x='t-SNE Dimension 1', y='t-SNE Dimension 2', hue=target_column, data=tsne_df, palette='viridis')
                plt.gca().set_facecolor('#ffffff')  # White background
                plt.title('t-SNE Analysis')
                st.pyplot(plt)
                buf = BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                st.download_button("Download t-SNE Figure", data=buf, file_name="tsne_analysis.png", mime="image/png")
            except Exception as e:
                st.error(f"An error occurred during t-SNE analysis: {e}")

        # PCA Analysis
        st.write("### 📊 PCA Analysis")
        if st.button("Run PCA Analysis"):
            try:
                pca = PCA(n_components=2)
                pca_results = pca.fit_transform(X)
                st.write("#### PCA Results Visualization")
                pca_df = pd.DataFrame(pca_results, columns=['PCA Component 1', 'PCA Component 2'])
                pca_df[target_column] = y
                plt.figure(figsize=(10, 6))
                sns.scatterplot(x='PCA Component 1', y='PCA Component 2', hue=target_column, data=pca_df, palette='viridis')
                plt.gca().set_facecolor('#ffffff')  # White background
                plt.title('PCA Analysis')
                st.pyplot(plt)
                buf = BytesIO()
                plt.savefig(buf, format="png")
                buf.seek(0)
                st.download_button("Download PCA Figure", data=buf, file_name="pca_analysis.png", mime="image/png")
            except Exception as e:
                st.error(f"An error occurred during PCA analysis: {e}")

        # Define algorithms
        if model_type == "Classification":
            models = {
                "RandomForest": RandomForestClassifier(max_depth=5, n_estimators=50),
                "DecisionTree": DecisionTreeClassifier(max_depth=5),
                "SVC": SVC(probability=True, kernel='linear'),
                "GaussianNB": GaussianNB(),
                "LogisticRegression": LogisticRegression(max_iter=1000),
                "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss')
            }
        else:
            models = {
                "RandomForest": RandomForestRegressor(max_depth=5, n_estimators=50),
                "DecisionTree": DecisionTreeRegressor(max_depth=5),
                "SVR": SVR(kernel='linear'),
                "LinearRegression": LinearRegression(),
                "XGBoost": XGBRegressor(objective='reg:squarederror')
            }

        if st.button("🚀 Train and Evaluate Multiple Models with Machine Learning"):
            st.markdown("### Machine Learning")
            try:
                # Train and evaluate models
                results = {}
                best_model_name = None
                best_accuracy = float('-inf')
                best_model = None
                for name, model in models.items():
                    if model is not None:
                        with st.spinner(f'Training {name} model...'):
                            model.fit(X_train, y_train)
                        y_pred_train = model.predict(X_train)
                        y_pred_test = model.predict(X_test)

                        # Calculate metrics
                        if model_type == "Classification" and len(np.unique(y_train)) > 2:
                            average_method = "weighted"  # Use weighted average for multiclass classification
                        else:
                            average_method = "binary"  # Use binary average for binary classification

                        if model_type == "Classification":
                            test_accuracy = accuracy_score(y_test, y_pred_test)
                            results[name] = {
                                "Train Accuracy": accuracy_score(y_train, y_pred_train),
                                "Test Accuracy": test_accuracy,
                                "Precision": precision_score(y_test, y_pred_test, average=average_method),
                                "Recall": recall_score(y_test, y_pred_test, average=average_method),
                                "F1-score": f1_score(y_test, y_pred_test, average=average_method),
                                "Brier Score": brier_score_loss(y_test, model.predict_proba(X_test)[:, 1]) if hasattr(model, 'predict_proba') and len(np.unique(y_test)) == 2 else None,
                                "AUC": roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]) if hasattr(model, 'predict_proba') and len(np.unique(y_test)) == 2 else None
                            }
                        else:
                            # Regression metrics
                            test_accuracy = model.score(X_test, y_test)  # R^2 score as accuracy
                            results[name] = {
                                "Train R2 Score": model.score(X_train, y_train),
                                "Test R2 Score": test_accuracy,
                                "MSE": mean_squared_error(y_test, y_pred_test),
                                "MAE": mean_absolute_error(y_test, y_pred_test),
                                "RMSE": np.sqrt(mean_squared_error(y_test, y_pred_test))
                            }

                        # Select the best model
                        if test_accuracy > best_accuracy:
                            best_accuracy = test_accuracy
                            best_model_name = name
                            best_model = model

                # Print results
                st.markdown("### 📊 Model Evaluation Results")
                st.markdown("#### Machine Learning Results")
                best_model_metrics = results[best_model_name]
                st.write(f"#### Best Model: {best_model_name}")
                for metric, value in best_model_metrics.items():
                    if value is not None:
                        st.write(f"{metric}: {value:.4f}")

                # SHAP Summary Plot (for Best Model)
                if best_model is not None:
                    st.write(f"### 🔍 SHAP Summary Plot for Best Model: {best_model_name}")
                    try:
                        explainer = shap.Explainer(best_model, X_train)
                        shap_values = explainer(X_test)
                        plt.figure()
                        shap.summary_plot(shap_values, X_test, feature_names=feature_columns, plot_type="bar", show=False)
                        plt.gca().set_facecolor('#ffffff')  # White background
                        plt.title('SHAP Summary Plot')
                        buf = BytesIO()
                        plt.savefig(buf, format="png")
                        buf.seek(0)
                        st.download_button("Download SHAP Summary Plot", data=buf, file_name="shap_summary_plot.png", mime="image/png")
                        st.pyplot(plt)
                    except Exception as e:
                        st.error(f"An error occurred during SHAP analysis: {e}")

                # LIME Analysis
                st.write("#### LIME Explanation for Best Model")
                if best_model is not None and hasattr(best_model, 'predict_proba'):
                    try:
                        explainer = lime.lime_tabular.LimeTabularExplainer(X_train, feature_names=feature_columns, class_names=['Control', 'Patient'], discretize_continuous=True)
                        exp = explainer.explain_instance(X_test[0], best_model.predict_proba if model_type == "Classification" else best_model.predict, num_features=10)
                        fig = exp.as_pyplot_figure()
                        fig.patch.set_facecolor('#ffffff')  # White background
                        plt.title('LIME Explanation Plot')
                        st.pyplot(fig)
                        buf = BytesIO()
                        fig.savefig(buf, format="png")
                        buf.seek(0)
                        st.download_button("Download LIME Explanation Plot", data=buf, file_name="lime_explanation_plot.png", mime="image/png")
                    except Exception as e:
                        st.error(f"An error occurred during LIME analysis: {e}")
                else:
                    st.warning("LIME cannot be applied because the selected model does not support probability scores.")

            except Exception as e:
                st.error(f"An error occurred during model training or evaluation: {e}")

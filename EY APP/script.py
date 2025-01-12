import numpy as np
import pandas as pd
import os
import cv2
from tqdm import tqdm
from pathlib import Path

import networkx as nx
import matplotlib.pyplot as plt
import seaborn as sns

import warnings
from collections import Counter

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout

from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

warnings.filterwarnings('ignore')

# Define utility class for styling and visualizations
class Utils:
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    END = "\033[0m"
    colors = ['pink', 'steelblue', 'hotpink', 'lightgreen', 'gray', 'salmon', 'gold', 'seagreen', 'skyblue', 'orchid']
    
    @staticmethod
    def explore_dataframe(df):
        print(f"{Utils.BOLD}Exploring DataFrame{Utils.END}")
        print(f"Shape: {df.shape}")
        print(f"Data Types:\n{df.dtypes}")
        print(f"Missing Values:\n{df.isnull().sum()}")
        print(f"Duplicate Rows: {df.duplicated().sum()}")
        print(f"Unique Values per Column:\n{df.nunique()}")
        display(df.describe())
    
    @staticmethod
    def visualize_distribution(data, x, title, xlabel, ylabel, colors=None, rotation=90):
        with plt.style.context('seaborn-whitegrid'):
            plt.figure(figsize=(15, 6))
            sns.set_palette(colors if colors else Utils.colors)
            sns.countplot(x=x, data=data)
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.xticks(rotation=rotation)
            plt.show()

    @staticmethod
    def visualize_date_distribution(data, date_column, title, xlabel, ylabel):
        with plt.style.context('seaborn-whitegrid'):
            plt.figure(figsize=(15, 6))
            sns.histplot(data[date_column], kde=True, bins=30, color='skyblue')
            plt.title(title)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.show()

    @staticmethod
    def visualize_top_values(data, condition_column, condition_value, count_column, top_n, title, xlabel, ylabel):
        subset = data[data[condition_column] == condition_value][count_column].value_counts().head(top_n)
        subset.plot(kind='barh', color='skyblue', figsize=(12, 6))
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()

# Load dataset
file_path = '/kaggle/input/flaredown-autoimmune-symptom-tracker/export.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
else:
    print("File not found. Please check the file path.")

# Preprocessing
df_object = df.select_dtypes(include=['object']).drop(columns=['user_id', 'country'], errors='ignore')
df[df_object.columns] = df_object.apply(lambda x: x.str.lower().str.strip())

# Filter data by country
unique_users_by_country = df.groupby('country')['user_id'].nunique()
countries_with_more_than_100_users = unique_users_by_country[unique_users_by_country > 100].index
filtered_df = df[df['country'].isin(countries_with_more_than_100_users)]

# Handle age data
filtered_df['age'] = filtered_df['age'].apply(lambda x: np.nan if x < 0 or x > 120 else x)
filtered_df['age'].fillna(filtered_df['age'].median(), inplace=True)

# Categorize age based on WHO standards
bins_WHO = [0, 5, 18, 30, 60, 120]
labels_WHO = ['babies', 'children', 'youth', 'adults', 'elderly']
filtered_df['age_category_WHO'] = pd.cut(filtered_df['age'], bins=bins_WHO, labels=labels_WHO, right=False)

# Visualize distributions
Utils.visualize_distribution(filtered_df, x='age_category_WHO', title='Age Distribution (WHO)', xlabel='Age Category', ylabel='Count')
Utils.visualize_distribution(filtered_df, x='sex', title='Sex Distribution', xlabel='Sex', ylabel='Count')

# Convert and visualize dates
filtered_df['checkin_date'] = pd.to_datetime(filtered_df['checkin_date'], errors='coerce')
Utils.visualize_date_distribution(filtered_df, date_column='checkin_date', title='Check-in Dates Distribution', xlabel='Date', ylabel='Frequency')

# Handle and visualize symptom data
if 'trackable_type' in filtered_df.columns and 'trackable_name' in filtered_df.columns:
    Utils.visualize_top_values(filtered_df, condition_column='trackable_type', condition_value='symptom', count_column='trackable_name', top_n=10, title='Top Symptoms', xlabel='Count', ylabel='Symptom')

# Display final dataframe
Utils.explore_dataframe(filtered_df)

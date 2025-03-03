# -*- coding: utf-8 -*-
"""product_defect_code

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1O47SM43JeDjTYkjZIgwAEhhGsP0ODuP2
"""

!pip install fastapi

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
import pandas as pd
import io

app = FastAPI()

# In-memory model and dataset
model = None
train_data = None

class PredictionRequest(BaseModel):
    Temperature: float
    Run_Time: float

!pip install python-multipart

# /upload endpoint: Accepts a CSV file and stores it in memory
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global train_data
    content = await file.read()
    # Load CSV into pandas DataFrame
    train_data = pd.read_csv("product_defect_data.csv")
    return {"filename": file.filename, "message": "File uploaded successfully"}

# Data Preprocessing Function
def preprocess_data(data: pd.DataFrame):
    # 1. Handle missing values (imputation)
    imputer = SimpleImputer(strategy="mean")  # Impute missing values with the mean
    data[['Temperature', 'Run_Time']] = imputer.fit_transform(data[['Temperature', 'Run_Time']])

    # 2. Feature scaling (Standardization)
    scaler = StandardScaler()
    data[['Temperature', 'Run_Time']] = scaler.fit_transform(data[['Temperature', 'Run_Time']])

    # 3. Optional: Remove any unnecessary columns or outliers
    # In this example, assuming Machine_ID is not needed for prediction
    data = data.drop(columns=['Machine_ID'], errors='ignore')

    return data

# /train endpoint: Trains the model and returns performance metrics
@app.post("/train")
async def train_model():
    if train_data is None:
        return {"error": "No data available. Please upload a dataset first."}

    # Prepare features and labels
    X = train_data[['Temperature', 'Run_Time']]
    y = train_data['Downtime_Flag']

    # Split data into training and testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train a Logistic Regression model
    global model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    return {"accuracy": accuracy, "f1_score": f1}

# /predict endpoint: Predicts downtime based on input data
@app.post("/predict")
async def predict_downtime(request: PredictionRequest):
    if model is None:
        return {"error": "Model has not been trained. Please train the model first."}

    # Prepare input data
    X_input = pd.DataFrame([[request.Temperature, request.Run_Time]], columns=['Temperature', 'Run_Time'])

    # Get prediction
    prediction = model.predict(X_input)
    confidence = model.predict_proba(X_input)[0][prediction[0]]

    # Return result in JSON format
    return {"Downtime": "Yes" if prediction[0] == 1 else "No", "Confidence": confidence}

!pip install uvicorn

# Main entry point (Optional, FastAPI can auto-generate docs)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
import json
import h2o
import pandas as pd
import requests
from flask import jsonify, request
from h2o.automl import H2OAutoML
from werkzeug.utils import secure_filename

h2o.init()


# Function to fetch and process data from the API
def fetch_and_process_data(data_url):
    response = requests.post(data_url)
    response.raise_for_status()
    data = response.json()

    # Extracting relevant information from the response
    buckets = data['aggregations']['2']['buckets']
    processed_data = []

    for bucket in buckets:
        timestamp = bucket['key_as_string']
        for sub_bucket in bucket['3']['buckets']:
            log_level = sub_bucket['key']
            count = sub_bucket['doc_count']
            processed_data.append({'@timestamp per day': timestamp, 'log_level': log_level, 'Count': count})

    return pd.DataFrame(processed_data)


# Function to train the models
def train_model(data_url):
    try:
        # Fetch and process data from external API
        df = fetch_and_process_data(data_url)
        df['@timestamp per day'] = pd.to_datetime(df['@timestamp per day'])
        df.set_index('@timestamp per day', inplace=True)

        warn_series = df[df['log_level'] == 'WARN'][['Count']]
        err_series = df[df['log_level'] == 'ERR'][['Count']]

        def train_automl(series):
            series['@timestamp per day'] = series.index.strftime('%Y-%m-%d')
            h2o_df = h2o.H2OFrame(series)
            target = 'Count'
            features = ['@timestamp per day']
            aml = H2OAutoML(max_models=20, seed=1)
            aml.train(x=features, y=target, training_frame=h2o_df)
            return aml.leader

        warn_model = train_automl(warn_series)
        err_model = train_automl(err_series)

        return warn_model, err_model
    except Exception as e:
        print(f"Error occurred while training models: {e}")
        return None, None


# Initial training of models
data_url = "http://localhost:5001/api/error_by_time"  # Replace with your actual data URL
warn_model, err_model = train_model(data_url)


# Function for prediction
def predict_count_service(log_level, steps):
    future_dates = pd.date_range(start=pd.Timestamp.now(), periods=steps + 1, freq='D')[1:]
    future_df = pd.DataFrame({'@timestamp per day': future_dates.strftime('%Y-%m-%d')})
    future_h2o_df = h2o.H2OFrame(future_df)

    if log_level.upper() == 'WARN':
        predictions = warn_model.predict(future_h2o_df)
    elif log_level.upper() == 'ERR':
        predictions = err_model.predict(future_h2o_df)
    else:
        return jsonify({'error': 'Invalid log_level'}), 400

    predicted_counts = predictions.as_data_frame().to_dict(orient='records')
    return jsonify(predicted_counts)

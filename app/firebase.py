import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore, storage
import streamlit as st
import pickle
import json
from google.oauth2 import service_account
pd.options.mode.chained_assignment = None  # default='warn'
from google.cloud import bigquery


def get_db_from_firebase_key(storage_bucket):
    key_dict = json.loads(st.secrets["firebase_key"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    firestore_client = firestore.Client(credentials=creds, project="amro-partners")
    storage_client = storage.storage.Client(credentials=creds, project="amro-partners")
    storage_bucket = storage_client.bucket(storage_bucket)
    return firestore_client, storage_bucket


def get_db_from_cert_file(cert_file, storage_bucket):
    # Use a service account
    try:
        app = firebase_admin.get_app()
    except ValueError as e:
        cred = credentials.Certificate(cert_file)

        try:
            firebase_admin.initialize_app(cred, {'storageBucket': storage_bucket})
        except ValueError as e:
            pass

    return firestore.client(), storage.bucket()


@st.cache_resource(show_spinner=False)
def read_and_unpickle(file_name, _storage_bucket):
    return pickle.loads(_storage_bucket.blob(file_name).download_as_string(timeout=300))


@st.cache_resource(show_spinner=False)
def read_and_unpickle(file_name, _storage_bucket):
    return pickle.loads(_storage_bucket.blob(file_name).download_as_string(timeout=300))


def bq_client(project):
    return bigquery.Client(project=project)


def send_bq_query(_client, query):
    return _client.query(query).to_dataframe()


def read_bq(_client, dataset_table, where_cond=None):
    if where_cond is None:
        where_cond = ""
    query = f"""
        SELECT *
        FROM {dataset_table}
        {where_cond}
    """
    # Fetch the data using the client object
    return send_bq_query(_client, query)

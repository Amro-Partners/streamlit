import os
import re
import streamlit as st
import times
import pandas as pd


@st.cache_data(show_spinner=False)
def read_consumption_codes(consumption_codes_file):
    path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(path, consumption_codes_file), encoding='latin-1').set_index('ADDRESS')['Title'].to_dict()


@st.cache_data(show_spinner=False)
def read_room_file(rooms_mapping_file):
    path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(path, rooms_mapping_file), encoding='latin-1')


@st.cache_data(show_spinner=False)
def get_floor_to_rooms_dict(rooms_mapping_file, floors_col):
    rooms_df = read_room_file(rooms_mapping_file)
    rooms_df = rooms_df[['ROOM', floors_col]].groupby(floors_col)['ROOM'].apply(list)
    return rooms_df.to_dict()

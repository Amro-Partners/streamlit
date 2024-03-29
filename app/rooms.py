import os
import streamlit as st
import pandas as pd


@st.cache_data(show_spinner=False, ttl=3600)
def get_ahu_dict(ahu_codes_file):
    path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(path, ahu_codes_file), encoding='latin-1').set_index('Title')['UNIT'].to_dict()


@st.cache_data(show_spinner=False, ttl=3600)
def read_room_file(rooms_mapping_file):
    path = os.path.dirname(__file__)
    return pd.read_csv(os.path.join(path, rooms_mapping_file), encoding='latin-1')


@st.cache_data(show_spinner=False, ttl=3600)
def get_group_to_rooms_dict(rooms_mapping_file, floors_col):
    rooms_df = read_room_file(rooms_mapping_file)
    rooms_df = rooms_df[['ROOM', floors_col]].groupby(floors_col)['ROOM'].apply(list)
    return rooms_df.to_dict()

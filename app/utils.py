import streamlit as st


@st.cache_data(show_spinner=False, ttl=3600)
def pivot_df(df, index, columns, values):
    df_pivot = df.pivot(index=index, columns=columns, values=values).sort_index()
    df_pivot.columns.name = None
    return df_pivot

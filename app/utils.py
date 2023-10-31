import streamlit as st


@st.cache_data(show_spinner=False, ttl=3600)
def pivot_df(df, index, columns, values):
    try:
        df_pivot = df.pivot(index=index, columns=columns, values=values).sort_index()
        df_pivot.columns.name = None
    except Exception as e:
        print(e)
        duplicate_indices = df.index[df.index.duplicated(keep=False)]
        print(duplicate_indices)
        
    
    return df_pivot

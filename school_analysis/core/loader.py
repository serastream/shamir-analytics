import pandas as pd
import streamlit as st

@st.cache_data
def load_uploaded_excel(file) -> dict:
    """Загружает все листы Excel-файла в словарь {sheet_name: DataFrame}"""
    xls = pd.ExcelFile(file)
    data = {sheet: xls.parse(sheet).loc[:, ~xls.parse(sheet).columns.duplicated()]
            for sheet in xls.sheet_names}
    return data

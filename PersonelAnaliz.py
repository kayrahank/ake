import streamlit as st
import pandas as pd
import os
from datetime import datetime
import numpy as np
import altair as alt
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import pytz

# Load the service account credentials from Streamlit secrets
service_account_info = st.secrets["service_account"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scopes=['https://www.googleapis.com/auth/drive']
)

# Initialize GoogleDrive instance with service account credentials
gauth = GoogleAuth()
gauth.credentials = credentials
drive = GoogleDrive(gauth)

# Define your Google Drive file IDs
EDATA_FILE_ID = '1la6L_Q-UTJGDoMHii3qPGCWRIAJP279h'
LOG_DATA_FILE_ID = '17hR9CanFUQ3FWfAkp7N4yREL2pXtd2-i'
USER_DATA_FILE_ID = '1_uqB3PerwPub1_ccEYo1XQ1eExe994wb'

st.set_page_config(
    page_title="Kurt-Ar Arama Kurtarma",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded")
st.title('Kurt-Ar Arama Kurtarma')
st.write('K.Kocyigit & M.Unsaldi')

t1, t2, t3 = st.tabs(["Kim Nerede?", "Kayıt Defteri", 'Görev Aksiyon Kaydı'])

# Read data directly from local CSV files
data = pd.read_csv("edata.csv")

if "Son Değişiklik" not in data.columns:
    data["Son Değişiklik"] = ""

def get_current_time_in_istanbul():
    istanbul_tz = pytz.timezone('Europe/Istanbul')
    return datetime.now(istanbul_tz).strftime("%Y-%m-%d %H:%M:%S")

def log_changes(old_data, new_data):
    common_cols = old_data.columns.intersection(new_data.columns)
    old_data = old_data[common_cols]
    new_data = new_data[common_cols]
    
    changes = new_data.compare(old_data)
    if not changes.empty:
        log_entries = []
        for index in changes.index:
            for column in changes.columns.levels[0]:
                old_value = changes.at[index, (column, 'self')]
                new_value = changes.at[index, (column, 'other')]
                if pd.isna(old_value) and pd.notna(new_value) or pd.notna(old_value) and pd.isna(new_value) or old_value != new_value:
                    log_entries.append({
                        "Tarih-Saat": get_current_time_in_istanbul(),
                        "Adı": new_data.iat[index, 1],  
                        "Soyadı": new_data.iat[index, 2],  
                        "Yapılan Değişiklik Türü": column,
                        "Yeni Değer": old_value,
                        "Eski Değer": new_value
                    })

                    new_data.at[index, "Son Değişiklik"] = get_current_time_in_istanbul()
        log_df = pd.DataFrame(log_entries)
        log_df.to_csv("log_data.csv", mode='a', header=not os.path.exists("log_data.csv"), index=False)

    return new_data

if 'old_data' not in st.session_state:
    st.session_state['old_data'] = data.copy()

def create_single_column_table(data):
    combined_names = data["Ad"] + " " + data["Soyad"]
    combined_namess = combined_names.tolist()
    explanations = data["Açıklama"].tolist()
    combined_data = list(zip(combined_namess, explanations))
    return pd.DataFrame(combined_data, columns=[f"Toplam kişi sayısı: {len(combined_names)}", "Açıklama"])

def create_two_column_table(data):
    combined_names = data["Ad"] + " " + data["Soyad"]
    combined_namess = combined_names.tolist()
    combined_namess += [""] * (len(combined_namess) % 2)
    combined_namess = np.array(combined_namess).reshape(-1, 2)
    return pd.DataFrame(combined_namess, columns=["Toplam kişi sayısı", f"{len(combined_names)}"])

def upload_file_to_drive(drive, file_path, file_id=None):
    if file_id:
        file = drive.CreateFile({'id': file_id})
    else:
        file = drive.CreateFile()
    file.SetContentFile(file_path)
    file.Upload()
    return file['id']

with t1:
    st.write("Kim Nerede?")

    edited = st.data_editor(data, use_container_width=True, hide_index=True, key="changedData", column_config={
        "Bulunduğu Yer": st.column_config.SelectboxColumn(
            "Bulunduğu Yer",
            help="Kişinin bulunduğu yer",
            width="medium",
            options=[
                "⛺ BoO",
                "🚧 Görev",
                "❔ Diğer",
            ],
            required=True,
        ),
        "Tim": st.column_config.SelectboxColumn(
            "Tim",
            help="Kişinin timi",
            width="medium",
            options=[
                "☝🏻️Tim-1",
                "✌🏻️Tim-2",
                "👔Yönetim",
                "⚙️Tim Dışı",
            ],
            required=True,
        ),
        "Açıklama": st.column_config.TextColumn(
            "Açıklama",
            help="Açıklama",
            width="large"
        )
    })

    if edited is not None and not edited.equals(st.session_state['old_data']):
        st.session_state['old_data'] = log_changes(st.session_state['old_data'], edited)
        st.session_state['old_data'].to_csv("edata.csv", index=False)
        st.experimental_rerun()
    
    st.divider()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("⛺BoO'da Bulunanlar")
        boo_data = data[data["Bulunduğu Yer"] == "⛺ BoO"]
        if not boo_data.empty:
            boo_table = create_two_column_table(boo_data)
            st.table(boo_table)
        else:
            st.write("BoO'da bulunan yok (NEDEN BOO'DA KİMSE YOK!)")

    with c2:
        st.write("🚧Göreve Gidenler")
        gorev_data = data[data["Bulunduğu Yer"] == "🚧 Görev"]
        if not gorev_data.empty:
            gorev_table = create_two_column_table(gorev_data)
            st.table(gorev_table)
        else:
            st.write("Göreve giden yok")

    with c3:
        st.write("❔Diğer")
        diger_data = data[data["Bulunduğu Yer"] == "❔ Diğer"]
        if not diger_data.empty:
            diger_table = create_single_column_table(diger_data)
            diger_table.index = diger_table.index + 1
            st.table(diger_table)
        else:
            st.write("Diğer kategorisinde kimse yok!")

    colmn1, colmn2, column3 = st.columns([2,3,2])
    chart_data = data["Bulunduğu Yer"].value_counts().reset_index()
    chart_data.columns = ["Bulunduğu Yer", "Kişi Sayısı"]

    pie_chart = alt.Chart(chart_data).mark_arc().encode(
        theta=alt.Theta(field="Kişi Sayısı", type="quantitative"),
        color=alt.Color(field="Bulunduğu Yer", type="nominal"),
        tooltip=["Bulunduğu Yer", "Kişi Sayısı"]
    )
    with colmn2:
        with st.expander("Bulunduğu Yer Bilgisine Göre Dağılım"):
            st.altair_chart(pie_chart)

with t2:
    st.write("Kayıt Defteri")
    if os.path.exists("log_data.csv") and os.path.getsize("log_data.csv") > 0:
        log_data = pd.read_csv("log_data.csv", names=["Tarih-Saat", "Adı", "Soyadı", "Yapılan Değişiklik Türü", "Yeni Değer", "Eski Değer"], header=0)
        
        st.dataframe(log_data, use_container_width=True)

        if not log_data.empty:
            row_to_delete = st.number_input("Silinecek Satır Numarası", min_value=0, max_value=len(log_data)-1, step=1, key="delete_log_row")
            if st.button("Seçili Satırı Sil", key="delete_log_button"):
                log_data = log_data.drop(row_to_delete).reset_index(drop=True)
                log_data.to_csv("log_data.csv", index=False)
                st.experimental_rerun()
    else:
        st.write("Henüz kayıt yok.")

with t3:
    if os.path.exists("user_data.csv"):
        user_data = pd.read_csv("user_data.csv")
    else:
        user_data = pd.DataFrame(columns=["Tarih - Saat", "Kaydı Giren", "Olay"])

    st.write("Yeni Kayıt Ekle")
    with st.form(key='my_form', clear_on_submit=True):
        user_name = st.text_input("Kaydı Giren Kişi")
        user_input = st.text_area("Görev Kaydı Girin")
        submit_button = st.form_submit_button(label='Ekle')

    if submit_button:
        timestamp = get_current_time_in_istanbul()
        new_entry = pd.DataFrame([[timestamp, user_name, user_input]], columns=["Tarih - Saat", "Kaydı Giren", "Olay"])
        user_data = pd.concat([user_data, new_entry], ignore_index=True)
        user_data.to_csv("user_data.csv", index=False)
        st.success("Yeni kayıt eklendi")
        st.experimental_rerun()

    if not user_data.empty:
        st.write("Kayıtlar:")
        st.dataframe(user_data, use_container_width=True)

        if len(user_data) > 0:
            row_to_delete = st.number_input("Silinecek Satır Numarası", min_value=0, max_value=len(user_data)-1, step=1, key="delete_user_row")
            if st.button("Seçili Satırı Sil", key="delete_user_button"):
                user_data = user_data.drop(row_to_delete).reset_index(drop=True)
                user_data.to_csv("user_data.csv", index=False)
                st.experimental_rerun()

if st.button("Tüm Dosyaları Google Drive ile Eşitle",type="primary"):
    upload_file_to_drive(drive, "edata.csv", EDATA_FILE_ID)
    upload_file_to_drive(drive, "log_data.csv", LOG_DATA_FILE_ID)
    upload_file_to_drive(drive, "user_data.csv", USER_DATA_FILE_ID)
    st.success("Kullanıcı dosyası Drive ile eşitlendi")

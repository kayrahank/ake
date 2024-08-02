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
import requests
from bs4 import BeautifulSoup
import folium
from streamlit_folium import folium_static
import plotly.express as px

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

t1, t2, t3, t4, t5 = st.tabs(["Kim Nerede?", "Kayıt Defteri", 'Görev Aksiyon Kaydı', "Deprem Haritası", "Hava Durumu"])

# Read data directly from local CSV files
data = pd.read_csv("edata.csv")

if "Son Değişiklik" not in data.columns:
    data["Son Değişiklik"] = ""

# Set default value for the "Açıklama" column
data["Açıklama"].fillna("açıklama", inplace=True)

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
                        "Yeni Değer": new_value,
                        "Eski Değer": old_value
                    })

                    new_data.at[index, "Son Değişiklik"] = get_current_time_in_istanbul()
        log_df = pd.DataFrame(log_entries)
        log_df.to_csv("log_data.csv", mode='a', header=not os.path.exists("log_data.csv"), index=False)

    return new_data

if 'old_data' not in st.session_state:
    st.session_state['old_data'] = data.copy()

def create_single_column_table(data):
    combined_names = data["Ad"] + " " + data["Soyad"] + " (" + data["Tim"] + ")"
    combined_namess = combined_names.tolist()
    explanations = data["Açıklama"].tolist()
    combined_data = list(zip(combined_namess, explanations))
    return pd.DataFrame(combined_data, columns=[f"Toplam kişi sayısı: {len(combined_names)}", "Açıklama"])

def create_two_column_table(data):
    combined_names = data["Ad"] + " " + data["Soyad"] + " (" + data["Tim"] + ")"
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
                "⚙️Lojistik",
            ],
            required=True,
        ),
        "Açıklama": st.column_config.TextColumn(
            "Açıklama",
            help=" ",
            width="large"
        )
    })

    if edited is not None and not edited.equals(st.session_state['old_data']):
        st.session_state['old_data'] = log_changes(st.session_state['old_data'], edited)
        st.session_state['old_data'].to_csv("edata.csv", index=False)
        st.experimental_set_query_params(rerun=True)
    
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
            row_to_delete = st.number_input("Silinecek Satır Numarası", min_value=0, max_value=len(log_data) - 1, step=1)
            if st.button("Satırı Sil"):
                log_data = log_data.drop(log_data.index[row_to_delete])
                log_data.to_csv("log_data.csv", index=False)
                st.experimental_set_query_params(rerun=True)
    else:
        st.write("Kayıt Defteri Boş")

with t3:
    st.write('Görev Aksiyon Kaydı')
    data_file = "User_data.csv"

    if os.path.exists(data_file):
        action_data = pd.read_csv(data_file)
    else:
        action_data = pd.DataFrame(columns=['Görev Konumu', 'Tarih ve Saat', 'Görev Türü', 'Görev Durumu'])

    new_row = {'Görev Konumu': '', 'Tarih ve Saat': '', 'Görev Türü': '', 'Görev Durumu': ''}
    action_data = pd.concat([action_data, pd.DataFrame([new_row])], ignore_index=True)

    action_data = st.data_editor(action_data, use_container_width=True, num_rows='dynamic')
    action_data.dropna(subset=['Görev Konumu', 'Tarih ve Saat', 'Görev Türü', 'Görev Durumu'], inplace=True)

    action_data.to_csv(data_file, index=False)

    st.divider()

    if os.path.exists(data_file):
        action_data = pd.read_csv(data_file)
        action_data.sort_values(by="Tarih ve Saat", ascending=False, inplace=True)

        if not action_data.empty:
            selected_row_index = st.number_input("Silinecek Satır Numarası", min_value=0, max_value=len(action_data) - 1, step=1)
            if st.button("Satırı Sil"):
                action_data = action_data.drop(action_data.index[selected_row_index])
                action_data.to_csv(data_file, index=False)
                st.experimental_set_query_params(rerun=True)

            filtered_action_data = action_data[action_data["Görev Türü"] == "Yapılan Görev"]
            if not filtered_action_data.empty:
                st.write("Son Yapılan Görevler")
                st.dataframe(filtered_action_data, use_container_width=True)
            else:
                st.write("Görev kaydı bulunamadı.")

        else:
            st.write("Görev Aksiyon Kaydı Boş")
    else:
        st.write("Görev Aksiyon Kaydı Bulunamadı")

# Deprem Haritası ve Hava Durumu Sekmeleri
with t4:
    st.header("Deprem Haritası")

    col1, col2 = st.columns([2, 2])

    with col1:
        url = "http://www.koeri.boun.edu.tr/scripts/lst0.asp"

        @st.cache_data(ttl=600)  # Cache data for 10 minutes (600 seconds)
        def load_data(url):
            response = requests.get(url)
            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                table = soup.find('pre')
                if table:
                    text_data = table.get_text()
                    rows = text_data.strip().split('\n')[6:]
                    data = []
                    for row in rows:
                        cols = row.split()
                        data.append(cols)
                    df = pd.DataFrame(data)
                    return df
            return None

        df = load_data(url)

        if df is not None:
            df.columns = ['Tarih', 'Saat', 'Enlem(N)', 'Boylam(E)', 'Derinlik(km)', 'MD', 'ML', 'Mw', 'Yer', 'Nitelik', 'Boş1', 'Boş2', 'Boş3', 'Boş4']
            df = df.drop(columns=['Boş1', 'Boş2', 'Boş3', 'Boş4'])
            df['Tarih'] = df['Tarih'].astype(str).str.strip()
            df['Saat'] = df['Saat'].astype(str).str.strip()
            df = df.dropna(subset=['Tarih', 'Saat'])
            df['TarihSaat'] = pd.to_datetime(df['Tarih'] + ' ' + df['Saat'], errors='coerce')
            df = df.dropna(subset=['TarihSaat'])
            df_last_24h = df[df['TarihSaat'] >= (pd.Timestamp.now() - pd.Timedelta(hours=24))]

            max_hours = st.slider("Son Kaç Saatteki Depremleri Gösterelim?", min_value=1, max_value=24, value=24, step=1)
            df_last_n_hours = df_last_24h[df_last_24h['TarihSaat'] >= (pd.Timestamp.now() - pd.Timedelta(hours=max_hours))]

            m = folium.Map(location=[39.0, 35.0], zoom_start=6)

            def get_color(magnitude):
                if magnitude < 2.0:
                    return 'green'
                elif 2.0 <= magnitude < 3.0:
                    return 'blue'
                elif 3.0 <= magnitude < 4.0:
                    return 'orange'
                else:
                    return 'red'

            for index, row in df_last_n_hours.iterrows():
                try:
                    color = get_color(float(row['ML']))
                    folium.CircleMarker(
                        location=[float(row['Enlem(N)']), float(row['Boylam(E)'])],
                        radius=5 + float(row['ML']) * 2,
                        popup=f"{row['Yer']} - ML: {row['ML']} - Saat: {row['Saat']}",
                        color=color,
                        fill=True,
                        fill_color=color
                    ).add_to(m)
                except ValueError:
                    continue

            folium_static(m)

            st.markdown("### Deprem Büyüklük Kategorileri ve Renkleri")
            st.markdown(
                """
                - **Yeşil:** 2.0'dan küçük depremler
                - **Mavi:** 2.0 - 2.9 arası depremler
                - **Turuncu:** 3.0 - 3.9 arası depremler
                - **Kırmızı:** 4.0 ve üzeri depremler
                """
            )
            
        else:
            st.write("Veri çekilemedi veya çekilen veri boş.")
    with col2:        
        st.dataframe(df_last_n_hours.drop(columns=['TarihSaat']))

with t5:
    st.header("Hava Durumu")

    col1, col2 = st.columns([2, 3])

    with col1:
        city = st.text_input("Şehir Adı", "İstanbul")

        @st.cache_data(ttl=600)  # Cache data for 10 minutes (600 seconds)
        def get_weather_data(city):
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid=92242406d0ed4c430bf77aaba84ed793&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return None

        @st.cache_data(ttl=600)  # Cache data for 10 minutes (600 seconds)
        def get_hourly_weather_data(city):
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid=92242406d0ed4c430bf77aaba84ed793&units=metric"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return None

        weather_data = get_weather_data(city)
        hourly_weather_data = get_hourly_weather_data(city)

        if weather_data:
            st.write(f"### {city} için Hava Durumu")
            st.write(f"**Sıcaklık:** {weather_data['main']['temp']}°C")
            st.write(f"**Hissedilen Sıcaklık:** {weather_data['main']['feels_like']}°C")
            st.write(f"**Nem:** {weather_data['main']['humidity']}%")
            st.write(f"**Hava Durumu:** {weather_data['weather'][0]['description'].capitalize()}")
            st.write(f"**Rüzgar Hızı:** {weather_data['wind']['speed']} m/s")
            st.write(f"**Rüzgar Yönü:** {weather_data['wind']['deg']}°")

    with col2:
        if weather_data and hourly_weather_data:
            st.write("### Saatlik Hava Tahmini")

            hourly_forecast = []
            for forecast in hourly_weather_data['list'][:24]:
                hourly_forecast.append({
                    "Saat": forecast['dt_txt'],
                    "Sıcaklık": forecast['main']['temp'],
                    "Hissedilen Sıcaklık": forecast['main']['feels_like'],
                    "Nem": forecast['main']['humidity'],
                    "Hava Durumu": forecast['weather'][0]['description'].capitalize(),
                    "Rüzgar Hızı": forecast['wind']['speed'],
                    "Rüzgar Yönü": forecast['wind']['deg']
                })
            hourly_df = pd.DataFrame(hourly_forecast)
            st.dataframe(hourly_df)
            
            fig_temp = px.line(hourly_df, x='Saat', y='Sıcaklık', title='Saatlik Sıcaklık Tahmini', labels={'Sıcaklık': 'Sıcaklık (°C)', 'Saat': 'Saat'})
            st.plotly_chart(fig_temp)
            
            fig_humidity = px.line(hourly_df, x='Saat', y='Nem', title='Saatlik Nem Tahmini', labels={'Nem': 'Nem (%)', 'Saat': 'Saat'})
            st.plotly_chart(fig_humidity)
            
            fig_wind = px.line(hourly_df, x='Saat', y='Rüzgar Hızı', title='Saatlik Rüzgar Hızı Tahmini', labels={'Rüzgar Hızı': 'Rüzgar Hızı (m/s)', 'Saat': 'Saat'})
            st.plotly_chart(fig_wind)

            weather_map = folium.Map(location=[weather_data['coord']['lat'], weather_data['coord']['lon']], zoom_start=10)
        else:
            st.write("Hava durumu bilgisi alınamadı.")

    with col1:
            for forecast in hourly_weather_data['list'][:24]:
                folium.Marker(
                    location=[weather_data['coord']['lat'], weather_data['coord']['lon']],
                    popup=f"Saat: {forecast['dt_txt']} - Sıcaklık: {forecast['main']['temp']}°C - Hava Durumu: {forecast['weather'][0]['description'].capitalize()}",
                    icon=folium.Icon(icon="cloud")
                ).add_to(weather_map)

            folium_static(weather_map)

# Add a button to clear the cache
if st.button("Veri önbelleğini temizle"):
    st.cache_data.clear()
    st.success("Veri önbelleği temizlendi, sayfayı yeniden yükleyin.")

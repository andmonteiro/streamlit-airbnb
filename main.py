import pandas as pd
import geopandas
import streamlit as st
import folium
import plotly.express as px

from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

#st.set_page_config(layout='wide')
DATA_URL = "https://raw.githubusercontent.com/anssodre/datasets/master/airbnb_rj.csv"
GEOJSON_URL = 'https://raw.githubusercontent.com/anssodre/datasets/master/Limite_de_Bairros.geojson'


@st.cache(allow_output_mutation=True)
def main():
    data = pd.read_csv(DATA_URL)
    return data


def get_geofile():
    geo = geopandas.read_file(GEOJSON_URL)
    return geo


# Load data
df = main()
geo = get_geofile()
rtype_label = df.room_type.unique().tolist()
neighbourhood_label = df.neighbourhood.sort_values().unique().tolist()

# Sidebar
info_sidebar = st.sidebar.empty()
price_filter = st.sidebar.slider('Escolha o valor máximo por noite: ', int(df.price.min()), int(df.price.max()))
st.sidebar.subheader("Tabela de Dados")
table = st.sidebar.empty()

room_type_filter = st.sidebar.multiselect(
    label="Escolha o tipo de lugar",
    options=rtype_label,
    default=rtype_label
)

filtered_df = df[(df.price <= price_filter) & (df.room_type.isin(room_type_filter))]

tb = filtered_df[['name', 'host_name', 'neighbourhood', 'room_type', 'price', 'minimum_nights']]
tb.columns = ['Descrição', 'Anfitrião', 'Bairro', 'Tipo de lugar', 'Valor', 'Mínimo de noites']

info_sidebar.info("{} opções carregadas.".format(filtered_df.shape[0], price_filter))

# Main
st.title("Airbnb - Rio de Janeiro")
st.markdown(f"""
            Estão sendo exibidos os lugares 
            de até **R${price_filter}** por noite""")

# Raw data
if table.checkbox("Exibir tabela de dados"):
    st.write(tb)

c1, c2 = st.beta_columns((1, 1))

c1.header('Mapa das hospedagens')
marker_map = folium.Map(location=[filtered_df['latitude'].mean(), filtered_df['longitude'].mean()],
                        tiles='cartodbpositron',
                        default_zoom_start=10,
                        )

marker_cluster = MarkerCluster().add_to(marker_map)
for name, row in filtered_df.iterrows():
    folium.Marker([row['latitude'], row['longitude']],
                  popup='Valor: R${0}/noite'.format(row['price'])
                  ).add_to(marker_cluster)

with c1:
    folium_static(marker_map, width=550)

c2.header('Mapa de densidade de preço')

density = filtered_df[['price', 'neighbourhood', 'latitude', 'longitude']].groupby('price').mean().reset_index()

# Filtra os bairros que somente estão no geojson e no df
geo = geo[geo['NOME'].isin(filtered_df['neighbourhood'].tolist())]

map_density = folium.Map(location=[filtered_df['latitude'].mean(), filtered_df['longitude'].mean()],
                         tiles='cartodbpositron',
                         default_zoom_start=10)
map_density.choropleth(data=filtered_df,
                       geo_data=geo,
                       columns=['neighbourhood', 'price', 'latitude', 'longitude'],
                       key_on='feature.properties.NOME',
                       fill_color='YlOrRd',
                       fill_opacity=0.5,
                       line_opacity=0.2,
                       legend_name='Média de preço',
                       popup='Valor: R${0}/noite'.format(['price']))
with c2:
    folium_static(map_density, width=550)

st.sidebar.subheader("Estatísticas")

# checkbox total por lugar
table_room_type = st.sidebar.empty()
if table_room_type.checkbox("Total por tipo de hospedagem"):
    fig = px.histogram(filtered_df, x='room_type',
                       labels={
                           'room_type': 'Tipo de hospedagem'
                       },
                       title='Tipo de hospedagem')
    st.plotly_chart(fig, use_container_width=True)

# checkbox bairros com mais hospedagem
table_neighborhood = st.sidebar.empty()
if table_neighborhood.checkbox("Hospedagem por bairro"):
    fig = px.histogram(filtered_df, x='neighbourhood',
                       labels={
                           'neighbourhood': 'Bairro'
                       },
                       title='Hospedagem por Bairro')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
from datetime import datetime
from collections import defaultdict, OrderedDict

# %%
import pandas as pd
import numpy as np

# %%
import plotly.io as pio
import plotly.express as px

# %%
import folium
from folium.plugins import HeatMap, HeatMapWithTime

# %%
pio.templates.default='plotly_dark'

# %%
URL = 'http://repositorio.dados.gov.br/seges/taxigov/taxigov-corridas-7-dias.zip'

# %%
df = pd.read_csv(URL, compression='zip')

# %%
#df[df.conteste_info.notna()]['conteste_info'][3772]

# %% [markdown]
# ## Limpeza de dados

# %%
df.dtypes

# %%
# coordenadas com vígula em vez de ponto
# df['origem_latitude'] = df['origem_latitude'].str.replace(',','.')

# %%
df['origem_latitude'] = df['origem_latitude'].astype(float)
df['origem_longitude'] = df['origem_longitude'].astype(float)

# %%
# coordenadas sem ponto decimal
# no_decimal = df.origem_latitude.apply(lambda s: '.' not in s)
# df.loc[no_decimal, 'origem_latitude'] = df[no_decimal]['origem_latitude'].apply(lambda s: s[:3] + '.' + s[3:])
for point_type in ('origem', 'destino_solicitado', 'destino_efetivo'):
    latitude_inexistente = df[f'{point_type}_latitude'] < -90.0, f'{point_type}_latitude'
    longitude_inexistente = df[f'{point_type}_longitude'] < -180.0, f'{point_type}_longitude'
    df.loc[latitude_inexistente] = df.loc[latitude_inexistente] / 100000.0
    df.loc[longitude_inexistente] = df.loc[longitude_inexistente] / 100000.0

# %%
# converte o que não for numérico
numeric_columns = ['origem_latitude', 'origem_longitude', 'destino_solicitado_latitude',
                   'destino_solicitado_longitude', 'destino_efetivo_latitude',
                   'destino_efetivo_longitude']
for column in numeric_columns:
    if df[column].dtype != 'float64':
        df[column] = df[column].apply(lambda s: pd.to_numeric(s) if isinstance(s, str) else s)

# %% [markdown]
# Ver quais são as bases de origem.

# %%
df.base_origem.unique()

# %%
df.sort_values('data_inicio', ascending=False).head()

# %%
len(df)

# %% [markdown]
# ## Motivos

# %%
motivos_df = df[df.base_origem == 'TAXIGOV_DF'].motivo_corrida.value_counts()
motivos_df

# %%
px.bar(motivos_df)

# %%
motivos_rj = df[df.base_origem == 'TAXIGOV_RJ_10'].motivo_corrida.value_counts()
motivos_rj

# %%
px.bar(motivos_rj)

# %%
motivos_sp = df[df.base_origem == 'TAXIGOV_SP_10'].motivo_corrida.value_counts()
motivos_sp

# %%
px.bar(motivos_sp)

# %% [markdown]
# ## Órgãos

# %%
orgaos_df = df[df.base_origem == 'TAXIGOV_DF'].nome_orgao.value_counts()
orgaos_df

# %%
px.bar(orgaos_df.iloc[:10])

# %% [markdown]
# > Obs.: Na base do DF está faltando a administração indireta.

# %%
orgaos_rj = df[df.base_origem == 'TAXIGOV_RJ_10'].nome_orgao.value_counts()
orgaos_rj

# %%
px.bar(orgaos_rj.iloc[:10])

# %%
orgaos_sp = df[df.base_origem == 'TAXIGOV_SP_10'].nome_orgao.value_counts()
orgaos_sp

# %%
px.bar(orgaos_sp)


# %% [markdown] tags=[]
# ## Mapas

# %% [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# ### Funções geradoras de mapas

# %%
def fares_map(df: pd.DataFrame) -> folium.Map:
    m = folium.Map(
        #location=[-15.7935,-47.8823],
        location=(
            (df.origem_latitude.mean() + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean() + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=11
    )

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora partida:<dt><dd>{corrida.data_inicio}</dd>'
                    f'<dt>Destino efetivo:<dt><dd>{corrida.destino_efetivo_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(m)
        coordinates = (corrida.destino_efetivo_latitude, corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora chegada:</dt><dd>{corrida.data_final}</dd>'
                    f'<dt>Origem:<dt><dd>{corrida.origem_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(m)

    return m


# %%
def fares_map_cluster(df: pd.DataFrame) -> folium.Map:
    m = folium.Map(
        location=(
            (df.origem_latitude.mean() + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean() + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=5
    )
    
    marker_cluster = folium.plugins.MarkerCluster().add_to(m)

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora partida:<dt><dd>{corrida.data_inicio}</dd>'
                    f'<dt>Destino efetivo:<dt><dd>{corrida.destino_efetivo_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(marker_cluster)
        coordinates = (corrida.destino_efetivo_latitude, corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora chegada:</dt><dd>{corrida.data_final}</dd>'
                    f'<dt>Origem:<dt><dd>{corrida.origem_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(marker_cluster)

    return m


# %%
def fares_map_category(df: pd.DataFrame, category_column: str) -> folium.Map:
    m = folium.Map(
        location=(
            (df.origem_latitude.mean() + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean() + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=5
    )

    group = {}
    for category in df[category_column].unique():
        feature_group = folium.FeatureGroup(category, show=False)
        feature_group.add_to(m)
        group[category] = feature_group

    for corrida in df.itertuples():
        coordinates = (corrida.origem_latitude, corrida.origem_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora partida:<dt><dd>{corrida.data_inicio}</dd>'
                    f'<dt>Destino efetivo:<dt><dd>{corrida.destino_efetivo_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='darkblue', icon='glyphicon glyphicon-log-out')
            ).add_to(group[getattr(corrida,category_column)])
        coordinates = (corrida.destino_efetivo_latitude, corrida.destino_efetivo_longitude)
        if not np.isnan(coordinates).any():
            folium.Marker(
                coordinates,
                popup=(
                    '<dl>'
                    f'<dt>Hora chegada:</dt><dd>{corrida.data_final}</dd>'
                    f'<dt>Origem:<dt><dd>{corrida.origem_endereco}</dd>'
                    f'<dt>Motivo:</dt><dd>{corrida.motivo_corrida}</dd>'
                    f'<dt>Distância:</dt><dd>{corrida.km_total}</dd>'
                    f'<dt>Valor:</dt><dd>{corrida.valor_corrida}</dd>'
                    '</dl>'
                ),
                icon=folium.Icon(color='orange', icon='glyphicon glyphicon-log-in')
            ).add_to(group[getattr(corrida,category_column)])

    folium.LayerControl().add_to(m)

    return m


# %%
def heat_map(df: pd.DataFrame, point_type: str) -> folium.Map:
    m = folium.Map(
        location=(
            (df.origem_latitude.mean() + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean() + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=11
    )
    
    df_notna = (
        df
        .loc[df[f'{point_type}_latitude'].notna()] # tira os nulos
        .loc[df[f'{point_type}_longitude'].notna()] # tira os nulos
        .loc[df['data_inicio'].notna()] # tira os nulos
    )

    HeatMap(
        df_notna
        .loc[:,[f'{point_type}_latitude', f'{point_type}_longitude']]
    ).add_to(m)

    return m


# %%
def heat_map_with_time(df: pd.DataFrame, point_type: str) -> folium.Map:
    m = folium.Map(
        location=(
            (df.origem_latitude.mean() + df.destino_efetivo_latitude.mean()) / 2,
            (df.origem_longitude.mean() + df.destino_efetivo_longitude.mean()) / 2
        ),
        zoom_start=6
    )
    
    # tira os nulos
    df_notna = (
        df
        .loc[df[f'{point_type}_latitude'].notna()]
        .loc[df[f'{point_type}_longitude'].notna()]
        .loc[df['data_inicio'].notna()]
    )
    
    # prepara estrutura de dados do HeatMapWithTime
    data = defaultdict(list)
    for index, row in df_notna.iterrows():
        data[datetime.fromisoformat(row['data_inicio']).date().strftime("%Y-%m-%d")].append([
            row[f'{point_type}_latitude'],
            row[f'{point_type}_longitude']
        ])
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    
    HeatMapWithTime(
        data=list(data.values()),
        index=list(data.keys()),
        auto_play=True,
    ).add_to(m)

    return m


# %% [markdown] tags=[]
# ### Mapa de calor geral

# %% tags=[]
m = heat_map(df.iloc[:], 'origem')
m.fit_bounds(m.get_bounds())
m


# %% tags=[]
m = heat_map_with_time(df.iloc[:], 'origem')
m


# %% [markdown] tags=[]
# ### Com clusters

# %% [markdown]
# Quando há muitos pontos no mapa, é útil poder visualizá-los em agrupamentos.

# %% tags=[]
m = fares_map_cluster(df)
m

# %% [markdown] tags=[]
# ### Por órgão

# %%
m = fares_map_category(df, 'nome_orgao')
m

# %% [markdown]
# #### Serviço Florestal Brasileiro em Brasília

# %%
corridas_servico_florestal = df[df.nome_orgao == 'Serviço Florestal Brasileiro']
corridas_servico_florestal.head()

# %%
fares_map(corridas_servico_florestal)

# %% [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# #### Itamaraty em Brasília

# %%
fares_map(df[df.nome_orgao=='Ministério das Relaçoes Exteriores'])

# %% [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# #### Ministério da Saúde no Rio de Janeiro

# %%
fares_map(df[df.nome_orgao=='2000-30-M.SAUDE'])

# %% [markdown] jp-MarkdownHeadingCollapsed=true tags=[]
# #### Anvisa em São Paulo

# %% tags=[]
fares_map(df[df.nome_orgao=='ANVISA'])

# %%
df[df.nome_orgao=='ANVISA']['motivo_corrida'].value_counts()

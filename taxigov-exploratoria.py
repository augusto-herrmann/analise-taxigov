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
import pandas as pd
import numpy as np

# %%
import plotly.express as px

# %%
import folium

# %%
URL = 'http://repositorio.dados.gov.br/seges/taxigov/taxigov-corridas-2021-11.zip'

# %%
df = pd.read_csv(URL, compression='zip')

# %% [markdown]
# ## Limpeza de dados

# %%
df.dtypes

# %%
# coordenadas com vígula em vez de ponto
df['origem_latitude'] = df['origem_latitude'].str.replace(',','.')

# %%
# coordenadas sem ponto decimal
no_decimal = df.origem_latitude.apply(lambda s: '.' not in s)
df.loc[no_decimal, 'origem_latitude'] = df[no_decimal]['origem_latitude'].apply(lambda s: s[:3] + '.' + s[3:])

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

# %% [markdown]
# ## Motivos

# %%
df[df.base_origem == 'TAXIGOV_DF'].motivo_corrida.value_counts()

# %%
motivos_rj = df[df.base_origem == 'TAXIGOV_RJ_10'].motivo_corrida.value_counts()
motivos_rj

# %%
px.bar(motivos_rj, template='plotly_dark')

# %%
df[df.base_origem == 'TAXIGOV_SP_10'].motivo_corrida.value_counts()

# %% [markdown]
# ## Órgãos

# %%
df[df.base_origem == 'TAXIGOV_DF'].nome_orgao.value_counts()

# %% [markdown]
# > Obs.: Na base do DF está faltando a administração indireta.

# %%
df[df.base_origem == 'TAXIGOV_RJ_10'].nome_orgao.value_counts()

# %%
df[df.base_origem == 'TAXIGOV_SP_10'].nome_orgao.value_counts()


# %% [markdown] tags=[]
# ## Mapas

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


# %% [markdown]
# Serviço Florestal Brasileiro em Brasília

# %%
corridas_servico_florestal = df[df.nome_orgao == 'Serviço Florestal Brasileiro']
corridas_servico_florestal.head()

# %%
fares_map(corridas_servico_florestal)

# %% [markdown]
# Itamaraty em Brasília

# %%
fares_map(df[df.nome_orgao=='Ministério das Relaçoes Exteriores'])

# %% [markdown]
# Ministério da Saúde no Rio de Janeiro

# %%
fares_map(df[df.nome_orgao=='2000-30-M.SAUDE'])

# %% [markdown]
# Anvisa em São Paulo

# %%
fares_map(df[df.nome_orgao=='ANVISA'])

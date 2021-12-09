# Análise de dados do Taxigov

Este repositório contém os cadernos Jupyter usados no projeto de análise
de dados do Taxigov.

## Conjunto de dados

O conjunto de dados utilizado são os
[dados do TaxiGov](https://dados.gov.br/dataset/corridas-do-taxigov)
publicados no Portal Brasileiro de Dados Abertos, atualizado diariamente.

## Para abrir

Para abrir os cadernos Jupyter utilize a extensão do Jupyter chamada
[Jupytext](https://jupytext.readthedocs.io/).

Para sua conveniência, você pode usar o
[ambiente com o Docker](https://github.com/augusto-herrmann/docker-jupyter-extensible)
que eu preparei, pois ele já vem pré-configurado com o Jupytext, dentre
outros pacotes úteis que são utilizados na análise (ex. Plotly, Folium).

No Jupyter Lab, clique com o botão direito sobre o arquivo `.py` e
selecione "Open With...", "Notebook".

Por que usamos o Jupytext? Pois os arquivos têm um tamanho muito menor,
onerando e pesando menos os arquivos do repositório. Além disso,
funciona melhor com o Git, pois é possível diferenciar linha a linha
para fazer o controle de versões.

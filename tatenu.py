import streamlit as st
import gspread
import pandas as pd
import numpy as np
import plotly.express as px


CODE = '1uhxc-2hRPXX8zpPBjeXDAOtW5zBAb_EhP3pLtbx4-U8'

gc = gspread.service_account(filename='key.json')

sh = gc.open_by_key(CODE)

ws = sh.worksheet('DATAFRAME')

df = pd.DataFrame(ws.get_all_records())



print(df)
# Ajuste: Dividir os valores por 100 na coluna 'PREÇO ATUAL' e 'DIVIDENDO'
df['PREÇO ATUAL'] = df['PREÇO ATUAL'] / 100
df['DIVIDENDO'] = df['DIVIDENDO'] / 100

# Função para calcular investimento necessário
def calcular_investimento(valor_codigo, rendimento_desejado, df):
    valores_codigo_selecionados = [codigo.strip() for codigo in valor_codigo]
    st.write("Códigos selecionados:", valores_codigo_selecionados)
    
    # Verificar se os códigos selecionados estão presentes no DataFrame
    codigos_validos = df['CÓDIGO'].unique()
    st.write("Códigos no DataFrame:", codigos_validos)
    if not set(valores_codigo_selecionados).issubset(codigos_validos):
        st.warning("Um ou mais códigos selecionados não estão presentes no DataFrame. Verifique os códigos e tente novamente.")
        return None

    # Remover espaços em branco dos códigos no DataFrame
    df.loc[:, 'CÓDIGO'] = df['CÓDIGO'].str.strip()

    valores_requeridos = df.loc[df['CÓDIGO'].isin(valores_codigo_selecionados), ['CÓDIGO', 'PREÇO ATUAL', 'DIVIDENDO']].copy()

    if valores_requeridos.empty:
        st.warning("Nenhuma entrada encontrada para os códigos fornecidos. Verifique os códigos e tente novamente.")
        return None

    valores_requeridos['Investimento Necessário'] = (rendimento_desejado / valores_requeridos['DIVIDENDO']) * valores_requeridos['PREÇO ATUAL']
    return valores_requeridos

# Função para filtrar o DataFrame pelo setor selecionado
def filtrar_por_setor(setor_selecionado, df):
    df_filtrado_por_setor = df[df['SETOR'] == setor_selecionado]
    return df_filtrado_por_setor

# Interface do Streamlit
st.sidebar.title("Parâmetros")

valores_padrao = df.iloc[1][['SETOR', 'PREÇO ATUAL', 'DIVIDENDO']]

valores_codigo_selecionados = st.sidebar.multiselect("Selecione os códigos:", df['CÓDIGO'].unique())
rendimento_desejado = st.sidebar.number_input("Digite o valor do rendimento desejado:", value=valores_padrao['DIVIDENDO'])

# Ajuste: Calculando os quartis para os valores de 'PREÇO ATUAL' e 'DIVIDENDO'
preco_minimo_q, preco_maximo_q = df['PREÇO ATUAL'].quantile([0.25, 0.75])
dividendo_minimo_q, dividendo_maximo_q = df['DIVIDENDO'].quantile([0.25, 0.75])

# Definindo margem extra para os valores mínimos e máximos
margem_extra = 0.5  # Por exemplo, 0,5

# Adicionando margem extra aos valores mínimos e máximos
preco_minimo = max(0, preco_minimo_q - margem_extra)
preco_maximo = preco_maximo_q + margem_extra
dividendo_minimo = max(0, dividendo_minimo_q - margem_extra)
dividendo_maximo = dividendo_maximo_q + margem_extra

# Adicionando barras deslizantes para os parâmetros de filtragem
preco_minimo, preco_maximo = st.sidebar.slider("Faixa de Preço", preco_minimo, preco_maximo, (preco_minimo, preco_maximo))
dividendo_minimo, dividendo_maximo = st.sidebar.slider("Faixa de Dividendo", dividendo_minimo, dividendo_maximo, (dividendo_minimo, dividendo_maximo))

setor_selecionado = st.sidebar.selectbox("Selecione o setor:", [''] + list(df['SETOR'].unique()))  # Adicionando uma opção em branco

# Filtrando o DataFrame com base nos parâmetros selecionados
df_filtrado = df[(df['PREÇO ATUAL'] >= preco_minimo) & (df['PREÇO ATUAL'] <= preco_maximo) & 
                 (df['DIVIDENDO'] >= dividendo_minimo) & (df['DIVIDENDO'] <= dividendo_maximo)]

# Filtrando também pelo setor selecionado
if setor_selecionado:
    df_filtrado = filtrar_por_setor(setor_selecionado, df_filtrado)

# Exibindo o DataFrame filtrado
st.subheader("DataFrame Filtrado")
st.write(df_filtrado)

if st.sidebar.button("Calcular"):
    valores_requeridos = calcular_investimento(valores_codigo_selecionados, rendimento_desejado, df_filtrado)
    if valores_requeridos is not None:
        st.title("Resultados")
        if valores_requeridos.empty:
            st.warning("Nenhum resultado encontrado para os códigos fornecidos. Verifique os códigos e tente novamente.")
        else:
            st.success("Investimento necessário para cada código selecionado:")
            st.write(valores_requeridos)

            fig = px.bar(valores_requeridos, x='CÓDIGO', y='Investimento Necessário', title='Investimento Necessário por Código')
            st.plotly_chart(fig)
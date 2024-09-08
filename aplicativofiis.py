import streamlit as st
import pandas as pd
import yfinance as yf

# Função modificada para carregar tickers de FIIs a partir de um arquivo CSV
def carregar_tickers_fiis():
    df = pd.read_csv('fii.csv')
    tickers_fiis = df['CODIGO'].tolist()
    return tickers_fiis

# Função de carregamento de dados
@st.cache
def carregar_dados_fiis(fiis):
    texto_tickers = " ".join(fiis)
    dados_fiis = yf.Tickers(texto_tickers)
    cotacoes_fiis = dados_fiis.history(period="1d", start="2010-01-01", end="2024-07-01")
    return cotacoes_fiis

# Função para coletar informações adicionais (setor, rendimento mensal, etc.)
def obter_informacoes_fiis(fii):
    ticker = yf.Ticker(fii)
    info = ticker.info
    resultado = {
        "preco_cota": info.get("currentPrice") or info.get("previousClose", 0),
        "rendimento_anual": info.get("dividendRate", 0),
        "rendimento_mensal": info.get("dividendRate", 0) / 12 if info.get("dividendRate", 0) else 0
    }
    return resultado

# Carregar tickers e dados dos FIIs
fiis = carregar_tickers_fiis()

# Carregar informações de todos os FIIs por padrão
informacoes_fiis = []
for fii in fiis:
    info = obter_informacoes_fiis(fii)
    informacoes_fiis.append({
        "Ticker": fii,
        "cota": info["preco_cota"],
        "dividendo": info["rendimento_mensal"],
    })

# Criar DataFrame para exibir as informações
df_informacoes = pd.DataFrame(informacoes_fiis)
df_informacoes["cota"] = df_informacoes["cota"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
df_informacoes["dividendo"] = df_informacoes["dividendo"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")

# Interface do Streamlit
st.write("""
# Informações sobre FIIs
Aqui estão as informações relevantes dos FIIs selecionados.
""")

st.sidebar.header("Filtros")
selecionar_todos = st.sidebar.checkbox("Selecionar todos", value=True)
if selecionar_todos:
    lista_fiis = st.sidebar.multiselect("Escolha os FIIs para visualizar", fiis, default=fiis)
else:
    lista_fiis = st.sidebar.multiselect("Escolha os FIIs para visualizar", fiis)

df_filtrado = df_informacoes[df_informacoes["Ticker"].isin(lista_fiis)]

# Adição dos controles deslizantes para preço e dividendo
preco_minimo = st.sidebar.slider("Preço mínimo", min_value=0, max_value=500, value=10)
preco_maximo = st.sidebar.slider("Preço máximo", min_value=0, max_value=500, value=50)
dividendo_minimo = st.sidebar.slider("Dividendo mínimo", min_value=0.0, max_value=10.0, value=1.0)
dividendo_maximo = st.sidebar.slider("Dividendo máximo", min_value=0.0, max_value=10.0, value=3.0)

# Função para filtrar o DataFrame baseado nos filtros selecionados
def filtrar_dados(df):
    return df[(df['cota'].astype(float) >= preco_minimo) & 
              (df['cota'].astype(float) <= preco_maximo) & 
              (df['dividendo'].astype(float) >= dividendo_minimo) & 
              (df['dividendo'].astype(float) <= dividendo_maximo)]

df_filtrado = filtrar_dados(df_filtrado)
st.dataframe(df_filtrado)

# Interface para cálculo de investimento necessário
st.sidebar.title("Cálculo de Investimento Necessário")
valores_codigo_selecionados = st.sidebar.multiselect('Selecione os Códigos dos Fundos', df_informacoes['Ticker'].unique())
rendimento_desejado_valor = st.sidebar.number_input('Insira o Rendimento Desejado', min_value=0.0, value=1000.0, step=100.0)

def calcular_investimento(valores_codigo_selecionados, rendimento_desejado, df):
    valores_requeridos = df.loc[df['Ticker'].isin(valores_codigo_selecionados), ['Ticker', 'cota', 'dividendo']].copy()
    if valores_requeridos.empty:
        st.warning("Nenhuma entrada encontrada para os códigos fornecidos. Verifique os códigos e tente novamente.")
        return None
    valores_requeridos['Investimento Necessário'] = (rendimento_desejado / valores_requeridos['dividendo'].astype(float)) * valores_requeridos['cota'].astype(float)
    return valores_requeridos

if st.sidebar.button('Calcular'):
    resultado = calcular_investimento(valores_codigo_selecionados, rendimento_desejado_valor, df_filtrado)
    if resultado is not None:
        st.write("### Resultado do Cálculo de Investimento Necessário")
        st.dataframe(resultado)

# Interface para cálculo do rendimento desejado
st.sidebar.title("Cálculo do Rendimento Desejado")
codigo_selecionado = st.sidebar.selectbox('Selecione o Código do Fundo', df_informacoes['Ticker'].unique())
valor_para_investir = st.sidebar.number_input('Insira o Valor para Investir', min_value=0.0, value=1000.0, step=100.0)

def rendimento_desejado(codigo, valor_para_investir, df):
    if codigo in df['Ticker'].values:
        valor_preco = df.loc[df['Ticker'] == codigo, 'cota'].astype(float).values[0]
        valor_rendimento = df.loc[df['Ticker'] == codigo, 'dividendo'].astype(float).values[0]
        numero_de_cotas = valor_para_investir / valor_preco
        rendimento_total = numero_de_cotas * valor_rendimento
        retorno_anual = rendimento_total * 12
        retorno_semestral = rendimento_total * 6
        retorno_trimestral = rendimento_total * 3
        retorno_mensal = rendimento_total
        st.write(f"O retorno em 1 mês é de R$ {retorno_mensal:.2f}")
        st.write(f"O retorno em 3 meses é de R$ {retorno_trimestral:.2f}")
        st.write(f"O retorno em 6 meses é de R$ {retorno_semestral:.2f}")
        st.write(f"O retorno em 12 meses é de R$ {retorno_anual:.2f}")
        st.write(f"Com R$ {valor_para_investir:.2f}, você pode comprar {numero_de_cotas:.2f} cotas.")
        st.write(f"O rendimento total estimado é de R$ {rendimento_total:.2f}.")
    else:
        st.error(f"O código {codigo} não está presente no DataFrame.")

if st.sidebar.button("Calcular Rendimento Desejado"):
    rendimento_desejado(codigo_selecionado, valor_para_investir, df_informacoes)
 
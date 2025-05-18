from dash import  html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import dash
from dash import html
from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from bcb import sgs

#Selecionar os Dados
IPCA = sgs.get({'IPCA':433}, start='2000-01-01').reset_index()
IPCAab = sgs.get({'IPCAab':1635}, start='2000-01-01').reset_index()
IPAM = sgs.get({'IPAM':7450}, start='2000-01-01').reset_index()
Ccb = sgs.get({'Custo Cesta Basica - SP':7493}, start='2000-01-01').reset_index()

#Limpar/Uniformizar os Dados
def datas(df, nome_coluna):
  df.columns = ['Data', nome_coluna]
  df['Data'] = pd.to_datetime(df['Data'])
  return df

dfipca = datas(IPCA, 'IPCA')
dfipcaab = datas(IPCAab, 'IPCA Alimentacao e Bebidas')
dfipam = datas(IPAM, 'IPA-M')
dfccb = datas(Ccb, 'Custo Cesta Basica - SP')

#Derivar os Dados
def variacao(df, nome_coluna, variacao):
  df[variacao] = df[nome_coluna].pct_change() *100
  return df

dfipca = variacao(dfipca, 'IPCA', 'Variacao IPCA')
dfipcaab = variacao(dfipcaab, 'IPCA Alimentacao e Bebidas', 'Variacao IPCA-AB')
dfipam = variacao(dfipam, 'IPA-M', 'Variacao IPA-M')
dfccb = variacao(dfccb, 'Custo Cesta Basica - SP', 'Variacao Custo Cesta Basica - SP')

#Integrar os Dados
dfintegrar = dfipca.merge(dfipcaab, on='Data', how='inner')
dfintegrar = dfintegrar.merge(dfipam, on='Data', how='inner')
dfintegrar = dfintegrar.merge(dfccb, on='Data', how='inner')

#Formatar os Dados
dfintegrar = dfintegrar.round(2)
dfipca = dfipca.round(2)
dfipcaab = dfipcaab.round(2)
dfipam = dfipam.round(2)
dfccb = dfccb.round(2)


df = dfintegrar

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

app.layout = html.Div(
    children=[
        html.H1("Análise de Indicadores Econômicos", style={
            "textAlign": "center",
            "marginBottom": "30px",
            "color": "#1f2937",
            "fontWeight": "bold",
            "fontSize": "2.5rem",
            "letterSpacing": "1px"
        }),

        dbc.Card([
            dbc.CardHeader("Configurações", style={
                "backgroundColor": "#f8f9fa",
                "fontWeight": "bold",
                "fontSize": "1.2rem"
            }),
            dbc.CardBody([
              
              dbc.Checklist(
    id='bcb',
    options=[
        {"label": "IPCA", "value": "IPCA"},
        {"label": "IPCA Alimentacao e Bebidas", "value": "IPCA Alimentacao e Bebidas"},
        {"label": "IPA-M", "value": "IPA-M"},
        {"label": "Custo Cesta Basica - SP", "value": "Custo Cesta Basica - SP"},
    ],
    value=["IPCA", "Custo Cesta Basica - SP"],
    inline=True,
    switch=True
),

dbc.RadioItems(
    id='grafico',
    options=[
        {"label": "Linha", "value": "line"},
        {"label": "Barra", "value": "bar"},
    ],
    value="line",
    inline=True
),

                html.Div([
                    html.H6("Filtrar por anos:", className="mb-2", style={"color": "#374151"}),
                    dcc.RangeSlider(
                        id='anos',
                        min=2000,
                        max=2025,
                        step=1,
                        value=[2000, 2024],
                        marks={i: str(i) for i in range(2000, 2026)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ])
            ])
        ], className="mb-4 shadow-sm"),

        dbc.Card([
            dbc.CardBody([
                dbc.Spinner(dcc.Graph(
                   id="graph",
                  figure={
                    "data": [],
                    "layout": {"title": "Gráfico vazio"}
                  }
                ), size="lg", color="primary", type="border")
            ])
        ], className="mb-4 shadow-sm"),

        dbc.Card([
            dbc.CardHeader("Correlação com a Cesta Básica", style={
                "backgroundColor": "#f8f9fa",
                "fontWeight": "bold",
                "fontSize": "1.2rem"
            }),
            dbc.CardBody([

dbc.RadioItems(
    id='bcbcorrelacao',
    options=[
        {"label": "IPCA", "value": "IPCA"},
        {"label": "IPCA Alimentacao e Bebidas", "value": "IPCA Alimentacao e Bebidas"},
        {"label": "IPA-M", "value": "IPA-M"},
    ],
    value="IPCA"
),
dcc.Graph(id="graphdois")

            ])
        ])
    ],
    style={
        "padding": "40px",
        "backgroundColor": "#f4f4f5",
        "minHeight": "100vh"
    }
)

@app.callback(
  Output('graph', 'figure'), Input('grafico', 'value'), 
  Input('bcb', 'value'), Input('anos', 'value')
)

def update_graph(tipo_grafico, opcoes_selecionadas, data_escolhida):
  fig = go.Figure()

  df_data = df[df['Data'].dt.year.between(data_escolhida[0], data_escolhida[1])]

  for op in opcoes_selecionadas:
      if op == "Custo Cesta Basica - SP":
        if tipo_grafico == 'line':
          fig.add_trace(go.Scatter(x=df_data["Data"], y=df_data[op], name=op, yaxis="y2", mode='lines'))
        elif tipo_grafico == 'bar':
          fig.add_trace(go.Bar(x=df_data["Data"], y=df_data[op], name=op, yaxis="y2", opacity=0.5))

      else:
        if tipo_grafico == 'line':
          fig.add_trace(go.Scatter(x=df_data["Data"], y=df_data[op], name=op, yaxis="y", mode='lines'))
        elif tipo_grafico == 'bar':
          fig.add_trace(go.Bar(x=df_data["Data"], y=df_data[op], name=op, yaxis="y"))

  fig.update_layout(xaxis=dict(title="Data"), yaxis=dict(title="Índices"),
                    yaxis2=dict(title="Cesta Básica (R$)", overlaying="y", side="right", showgrid=False),
                    title = "Evolução Temporal dos Índices Econômicos",
                    barmode="group" if tipo_grafico == "bar" else None,
                    template="plotly_white",
                    paper_bgcolor="#f8f9fa",
                    plot_bgcolor="#f0f0f0",
                    font=dict(family="Inter, sans-serif", size=13, color="#1f2937"),
                    margin=dict(l=40, r=40, t=50, b=40),
                    legend=dict(borderwidth=0, orientation="h", x=0.5, xanchor="center", y=-0.3),
  )

  fig.update_xaxes(dtick="M12" )
  return fig

@app.callback(
  Output('graphdois', 'figure'), [Input('bcbcorrelacao', 'value'), Input('anos', 'value')]
)

def update_graph2(opcoes_correlacao,anos):
  z = "Custo Cesta Basica - SP"
  y = opcoes_correlacao
  i = f"{y}"

  dfcorrelacao = df.copy()
  dfcorrelacao[y] = df[y] * 1000
  dfcorrelacao.rename(columns={y : i}, inplace=True)

  fig = px.scatter(dfcorrelacao, x="Data", y=[i,z],
                    trendline = "ols", title = f"Dispersão e Correlação: {z} e {i}", opacity = 0.5)
  
  fig.update_layout(legend=dict(orientation="h", yanchor="top", y=1, xanchor="center", x=0.5, bordercolor = "black", borderwidth=1), legend_title = None)
  fig.update_yaxes(visible = False)
  fig.update_xaxes(dtick = "M12" )
  return fig


if __name__ == '__main__':
  app.run(debug=True)

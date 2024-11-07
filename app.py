import dash
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np

# Cargar el dataset con 30 mujeres bolivianas y eliminar espacios en los nombres de las columnas
df_bolivia_30_women = pd.read_csv('Mujeres_STEM_Bolivia_corrected_coordinates.csv')
df_bolivia_30_women.columns = df_bolivia_30_women.columns.str.strip()  # Eliminar espacios en los nombres de columnas

# Mapa de colores únicos para cada mujer usando Plotly Express
colors = px.colors.qualitative.Prism
df_bolivia_30_women['Color'] = [colors[i % len(colors)] for i in range(len(df_bolivia_30_women))]

# Ajuste de latitudes/longitudes para evitar superposición en el mapa al ver toda Bolivia
def ajustar_lat_long(df, zoom):
    seen = {}
    factor = 0.01 if zoom <= 5 else 0.001  # Mayor dispersión al ver toda Bolivia
    for i, row in df.iterrows():
        key = (row['Latitud'], row.get('Longitud', 0))
        if key in seen:
            seen[key] += 1
            df.at[i, 'Latitud'] += np.random.uniform(-factor, factor) * seen[key]
            df.at[i, 'Longitud'] = row.get('Longitud', 0) + np.random.uniform(-factor, factor) * seen[key]
        else:
            seen[key] = 0
    return df

# Coordenadas de las ciudades para centrar el mapa en cada una al hacer zoom
city_coordinates = {
    'La Paz': {"lat": -16.5000, "lon": -68.1500, "zoom": 12},
    'Santa Cruz': {"lat": -17.7833, "lon": -63.1823, "zoom": 12},
    'Tarija': {"lat": -21.5333, "lon": -64.7333, "zoom": 12},
    'Todos': {"lat": -17.0, "lon": -65.0, "zoom": 5}  # Centro general para Bolivia
}

# Inicializar la aplicación Dash con un título y color de fondo
app = dash.Dash(__name__)
app.title = "Mujeres STEM Bolivia"
server = app.server

# Layout de la aplicación
app.layout = html.Div(style={'backgroundColor': '#f7f9fc', 'padding': '20px', 'font-family': 'Arial, sans-serif'}, children=[
    html.H1("Mujeres STEM en Bolivia", style={'text-align': 'center', 'color': '#333', 'font-size': '36px', 'margin-bottom': '10px'}),
    html.P("Una visualización de mujeres destacadas en el campo STEM en Bolivia", style={'text-align': 'center', 'color': '#555', 'font-size': '18px'}),
    
    # Filtro por campo STEM
    html.Div([
        html.Label('Filtrar por Campo STEM:', style={'font-weight': 'bold', 'color': '#333'}),
        dcc.Dropdown(
            id='filtro_stem',
            options=[{'label': i, 'value': i} for i in df_bolivia_30_women['Campo STEM'].unique()] + [{'label': 'Todos los campos', 'value': 'Todos los campos'}],
            value='Todos los campos',
            placeholder="Selecciona un campo STEM",
            style={'width': '50%', 'margin': 'auto', 'border-radius': '5px', 'font-size': '16px'}
        )
    ], style={'text-align': 'center', 'margin-bottom': '20px'}),
    
    # Filtro de ciudad
    html.Div([
        html.Label('Seleccionar ciudad:', style={'font-weight': 'bold', 'color': '#333'}),
        dcc.Dropdown(
            id='filtro_ciudad',
            options=[{'label': "Ver toda Bolivia", 'value': 'Todos'}] + [{'label': ciudad, 'value': ciudad} for ciudad in city_coordinates.keys() if ciudad != 'Todos'],
            value='Todos',
            placeholder="Selecciona una ciudad",
            style={'width': '50%', 'margin': 'auto', 'border-radius': '5px', 'font-size': '16px'}
        )
    ], style={'text-align': 'center', 'margin-bottom': '20px'}),
    
    # Gráfico del mapa
    dcc.Graph(id='mapa_interactivo', style={'height': '700px', 'border': '2px solid #ddd', 'border-radius': '10px', 'padding': '10px'}),

    # Tabla de logros destacados
    html.Div(id='tabla_logros', style={'text-align': 'center', 'margin-top': '20px'})
])

# Callback para actualizar el mapa y la tabla de logros
@app.callback(
    [Output('mapa_interactivo', 'figure'),
     Output('tabla_logros', 'children')],
    [Input('filtro_stem', 'value'),
     Input('filtro_ciudad', 'value')]
)
def update_map(filtro_stem, filtro_ciudad):
    # Filtrar dataset según campo STEM
    dff = df_bolivia_30_women.copy()
    if filtro_stem != 'Todos los campos':
        dff = dff[dff['Campo STEM'] == filtro_stem]
    
    # Obtener coordenadas y nivel de zoom según la ciudad seleccionada
    coord = city_coordinates.get(filtro_ciudad, city_coordinates['Todos'])

    # Ajuste de coordenadas para evitar superposición si se ve toda Bolivia
    dff = ajustar_lat_long(dff, coord['zoom'])

    # Mapa interactivo con colores únicos para cada mujer y enlaces personalizados
    fig = go.Figure(go.Scattermapbox(
        lat=dff['Latitud'],
        lon=dff['Longitud'],
        mode='markers',
        marker=dict(
            size=18,  # Tamaño aumentado para mayor visibilidad
            color=dff['Color'],
            opacity=0.85,
            symbol="circle"
        ),
        text=dff['Nombre'],
        hoverinfo='text',
        hovertext=dff.apply(lambda row: f"<b>{row['Nombre']}</b><br>{row['Campo STEM']}<br><i>Institución:</i> {row['Institución']}<br><i>Logros:</i> {row['Destacado']}", axis=1),
        customdata=dff['Contacto (página personal, otros)']
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",  # Estilo de mapa más claro
            zoom=coord['zoom'],
            center={"lat": coord['lat'], "lon": coord['lon']}
        ),
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False,
        height=600,
        paper_bgcolor='#f7f9fc'
    )

    # Crear tabla de logros destacados
    logros = dff[['Nombre', 'Destacado']].to_dict('records')
    tabla_logros = html.Table([
        html.Thead(html.Tr([html.Th('Nombre', style={'padding': '10px', 'border-bottom': '2px solid #ddd', 'color': '#333'}),
                            html.Th('Logros', style={'padding': '10px', 'border-bottom': '2px solid #ddd', 'color': '#333'})]))
    ] + [
        html.Tr([html.Td(fila['Nombre'], style={'padding': '10px', 'border-bottom': '1px solid #eee', 'text-align': 'center'}),
                 html.Td(fila['Destacado'], style={'padding': '10px', 'border-bottom': '1px solid #eee', 'text-align': 'center'})]) for fila in logros
    ], style={'width': '80%', 'margin': 'auto', 'border-collapse': 'collapse', 'backgroundColor': '#fff', 'border-radius': '10px', 'box-shadow': '0px 4px 8px rgba(0,0,0,0.1)'})
    
    return fig, tabla_logros

# JavaScript callback para abrir enlaces
app.clientside_callback(
    """
    function(clickData) {
        if (clickData) {
            const url = clickData.points[0].customdata;
            window.open(url, '_blank');
        }
    }
    """,
    Output('mapa_interactivo', 'clickData'),
    Input('mapa_interactivo', 'clickData')
)

# Ejecutar la aplicación en el puerto 9090
if __name__ == '__main__':
    app.run_server(debug=True, port=9090)


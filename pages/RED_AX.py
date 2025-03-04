from dash import Dash, dcc, html, Input, Output, callback, dash_table, register_page
import dash_cytoscape as cyto
import pandas as pd

# Cargar los datos desde Excel
#url='https://docs.google.com/spreadsheets/d/e/2PACX-1vS6jR4F7HMDXcVexiJmZ9plXuNX3ZO0yC4F8TwKf3eSr20GgCaMITByNdiFjmSqgA/pub?output=xlsx'
url='https://docs.google.com/spreadsheets/d/e/2PACX-1vTU0SdQdcULvuqk9abcnzdW609dHXszo-JEfvp0RkQAyR1maTr5m9eINsli_5iGKQ/pub?output=xlsx'
#df_d  = pd.read_excel('../BD_RED.xlsx', sheet_name='DEPENDIENTE')
#df_ipt =pd.read_excel('../BD_RED.xlsx', sheet_name='IPT-TDP')

df_d = pd.read_excel(url, sheet_name='DEPENDIENTE')
df_ipt = pd.read_excel(url, sheet_name='IPT-TDP')


register_page(__name__, path="/RED_AX")
layout = html.Div([
    html.Div([
        dcc.RadioItems(
            options=[{'label': 'VLAN', 'value': 'VLAN'},
                     {'label': 'ID', 'value': 'ID'},
                     {'label': 'DISTRITAL', 'value': 'DISTRITAL'}],
            value='DISTRITAL', 
            inline=True, 
            id='type_selection'
        ),

        dcc.Dropdown(id='selector-ax'),

        html.P(id='cytoscape-tapNodeData-output'),
        html.Pre(id='cytoscape-tapNodeData'),

    ], style={'width': '20%', 'display': 'inline-block','font-family': 'monospace'}),

    html.Div([
        cyto.Cytoscape(
        id='cytoscape-graph-ax',
        style={'width': '100%', 'height': '600px'},
        maxZoom=3,
        minZoom=0.5
        ,
        stylesheet=[
            {
                "selector": "node",
                "style": {
                    "content": "data(label)",
                    "background-color": "#229954",
                    "color": "#000000",
                    "text-valign": "top",
                    "text-halign": "center",
                    "width": "30px",
                    "height": "30px",
                }
            },
            {
                "selector": "edge",
                "style": {
                    "width": 2.5,
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle"
                }
            }
        ]
    )    
    ], style={'width': '80%' ,'display': 'inline-block', 'font-family': 'monospace', 'float': 'right'})
    
])

###TIPO DE SELECTOR
@callback(
    Output('selector-ax', 'options'),
    Output('selector-ax', 'value'),
    Input('type_selection', 'value')
)
def selector(type_selec):
    options = []
    default_value = None

    if type_selec == 'DISTRITAL':
        options = [{'label': d, 'value': i} for i, d in df_d[['ID', 'DISTRITAL']].drop_duplicates().dropna().values]
    elif type_selec == 'VLAN':
        options = [{'label': f"Vlan {d}", 'value': i} for i, d in df_ipt[['Codigo POP Coberturador', 'VLAN']].drop_duplicates().dropna().values]
    elif type_selec == 'ID':
        options = [{'label': f"{d}-A01", 'value': d} for d in pd.concat([df_d['SOURCE'], df_d['TANGET']]).drop_duplicates().dropna().values]

    if options:
        default_value = options[0]['value']  

    return options, default_value
    

@callback(
    Output('cytoscape-tapNodeData', 'children'),
    Output('cytoscape-graph-ax', 'stylesheet'),
    Input('cytoscape-graph-ax', 'tapNodeData'),
    Input('selector-ax', 'value'),
)
def displayTapNodeData(tapped_node,value_data):

    base_stylesheet = [
        {
            "selector": "node",
            "style": {
                "content": "data(label)",
                "background-color": "#229954",  
                "color": "#000000",
                "text-valign": "top",
                "text-halign": "center",
                "width": "30px",
                "height": "30px",
                
            }
        },
        {
            "selector": "edge",
            "style": {
                "width": 2.5,
                "curve-style": "bezier",
                "target-arrow-shape": "triangle"
            }
        }
    ]

    ####################################################
    
    if tapped_node:
        list_ax=[]
        lista_de_control=[]
        list_ax.append(tapped_node['id'])
    
        df_y=df_d[['SOURCE', 'TANGET']]
        lista_de_control= list_ax
        a=0
        while True:
            df_z = df_y[df_y['SOURCE'].isin(lista_de_control)].dropna()
            lista_de_control=[]
            if df_z.empty:
                break

            for ax in df_z['TANGET']:
                list_ax.append(ax)
                lista_de_control.append(ax)
       
        for i in list_ax:
            base_stylesheet.append({
                "selector": f"node[id = '{i}']",
                "style": {
                    "background-color": "#5dade2",  
                    "width": "30px",
                    "height": "30px",
                }
            })

    if value_data:
        base_stylesheet.append({
            "selector": f"node[id = '{value_data}']",
            "style": {
                "background-color": "#a569bd",
                "width": "30px",
                "height": "30px",
        }
    })    
    
   

    if tapped_node is None:
        return "Haz clic en un nodo para ver más detalles." ,base_stylesheet 
    node_id = tapped_node.get('id') 
    vlan =df_ipt[df_ipt['Codigo POP Coberturador'].isin(list_ax)][['VLAN', 'Codigo POP Coberturador', 'INTERFACE','CLIENTE']]

    if vlan.empty:
        return f"NODO {tapped_node['label'][:7]}, sin Vlan's de Clientes disponibles.", base_stylesheet

   

    tabla = dash_table.DataTable(
        style_data={
        'whiteSpace': 'normal',
        'height': 'auto',
        'lineHeight': '5px',
        'textAlign': 'left',
         },
        sort_action='native',
        data= vlan.to_dict('records'),
        columns= [{"name": i, "id": i} for i in vlan.columns],
        page_size=10
        )

    return tabla, base_stylesheet
 

@callback(
    Output('cytoscape-graph-ax', 'elements'),
    Output('cytoscape-graph-ax', 'layout'),
    Input('selector-ax', 'value'),
    Input('type_selection', 'value'),
)
def update_cytoscape_elements(selected_node, type_selec):
    if not selected_node:  
        return [], {'name': 'breadthfirst', 'directed': True}

    if type_selec == "DISTRITAL":
        dependents = df_d[df_d['ID'] == selected_node]
        root = selected_node

    elif type_selec == "ID":
        nodo_d = df_d.loc[df_d['SOURCE'] == selected_node, 'ID'].values
        if nodo_d.size == 0: 
            nodo_d = df_d.loc[df_d['TANGET'] == selected_node, 'ID'].values
            if nodo_d.size == 0:    
                return [], {'name': 'breadthfirst', 'directed': True} 
        root = nodo_d[0]
        dependents = df_d[df_d['ID'] == root]

    elif type_selec == "VLAN":
        nodo_d = df_ipt.loc[df_ipt['Codigo POP Coberturador'] == selected_node, 'Codigo NODO RAIZ'].values
        if nodo_d.size == 0: 
            return [], {'name': 'breadthfirst', 'directed': True}  
        root = nodo_d[0]
   
        dependents = df_d[df_d['ID'] == root]

    concate = pd.concat([dependents['SOURCE'], dependents['TANGET']])
    dependent_nodes = [{"data": {"id": dep, "label": f"{dep}-A01"}} for dep in concate.dropna().unique()]
    edges = [{"data": {"source": s, "target": t}} for s, t in dependents[['SOURCE', 'TANGET']].dropna().values]

    return dependent_nodes + edges, {
        'name': 'breadthfirst',
        'roots': f'#{root}',
        'directed': True,
        'spacingFactor': 2.5,
        'fit': True,
    }



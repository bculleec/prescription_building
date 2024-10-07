from dash import Dash, dash_table, dcc, html, Input, Output, callback
from dash.dash_table.Format import Format
import pandas as pd
from prescription_build import *

app = Dash(__name__)

p = Prescription()
z = []

r_path = "C:/Users/bculleechurn/Downloads/Ariss-Bicarb-P.tif"
z = read_zones(r_path, 2)

p = prescription_from_zones(z)

z.print_table()

p.print_table()

z.set_zone_rate(id = 1, rate = 10)
z.set_zone_rate(id = 2, rate = 20)
z.print_table()

p.auto_set_rates(zone_group=z)
p.print_table()

# Incorporate data
df = p.to_dataframe()

# Initialize the app
app = Dash()

params = ['Zone ID', 'Min Value in zone', 'Max Value in zone', 'Average value in zone', 'Total Acres', 'Lbs/Ac Product in Script']
params2 = ['Description', 'Value']

# App layout
app.layout = [
    html.Div(children='Zone Info'),
    dash_table.DataTable(id = "editing-grid", data=z.to_dataframe().to_dict('records'), columns = [{'id':p, 'name':p, 'on_change': {'action' : 'coerce', 'failure' : 'default'}, 'type' : 'numeric', 'format' : Format(precision = 5)} for p in params], page_size=10, editable=True),
    html.Div(children='Summary'),
    dash_table.DataTable(id = "prescription-grid", data=df.to_dict('records'),  columns = [{'id':p, 'name':p, 'on_change': {'action' : 'coerce', 'failure' : 'default'}, 'type' : 'numeric', 'format' : Format(precision = 5)} for p in params2], page_size=10, editable=True)
]

# Case user updates Zone Table
@callback(
    Output("prescription-grid", "data"),
    Input("editing-grid", "data"),
    Input("editing-grid", 'columns')
)
def update(rows, columns):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    print(df)

    # Recalculate the prescription based on the new values
    new_prescription = Prescription()
    new_prescription.auto_set_rates(zones_from_df(df))

    df = new_prescription.to_dataframe()

    # Render the prescriptions table with new_prescription
    return (new_prescription.to_dataframe().to_dict('records'))

# Case user updates Prescription Table
@callback(
    # Output("prescription-grid", "data"),
    Input("prescription-grid", "data"),
    Input("prescription-grid", "columns"),
    
)
def update_prescription(rows, columns):
    print("Old Table")
    print(df)
    print()

    print("New Table")
    print(pd.DataFrame(rows, columns=[c['name'] for c in columns]))

    new_df = pd.DataFrame(rows, columns=[c['name'] for c in columns])

    df = new_df
    new_prescription = prescription_from_df(new_df)

    print("New Prescription")
    print(new_prescription.to_dataframe())


    # Detect if average rate has been changed
    if (df['Value'][0] != new_df['Value'][0]):
        new_prescription = new_prescription.auto_update(changed_param = "AVERAGE", changed_ratio=new_df['Value'][0] / df['Value'][0])
        print(new_prescription.to_dataframe())
        
    # return (new_prescription.to_dataframe().to_dict('records'))
    # Update the Zone grid

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
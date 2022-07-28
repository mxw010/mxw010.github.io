import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json
import numpy as np

#import county polygon data
with urlopen(
        'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
) as response:
    counties = json.load(response)
# state ID

state = pd.read_excel(
    'https://www2.census.gov/programs-surveys/popest/geographies/2020/state-geocodes-v2020.xlsx',
    header=5)

#read in population change data
pop = pd.read_excel(
    'https://www2.census.gov/programs-surveys/popest/tables/2010-2019/counties/totals/co-est2019-comp.xlsx',
    header=5)
pop = pop.iloc[1:3143, 0:8]
pop.columns = [
    'County', 'tot_change', 'Natural', 'Births', 'Deaths', 'Migration_total',
    'International', 'Domestic'
]

#split State and County
pop['State'] = [x.split(", ")[1] for x in pop['County']]
pop.iloc[:, 0] = [x.split(", ")[0].replace(".", "") for x in pop['County']]

# Total Population
tot = pd.read_excel(
    'https://www2.census.gov/programs-surveys/popest/tables/2010-2019/counties/totals/co-est2019-annres.xlsx',
    header=3)
tot_pop = tot.iloc[1:3143, 3]
pop['tot_pop'] = tot_pop

code = []
for item in pop['State']:
    code.append(state[state['Name'] == item].iloc[0, 2])
    # if y < 10:
    #     code.append('0'+ str(y))
    # else:
    #     code.append(str(y))

pop['State_code'] = code

#getting fips for population change data
fips_all = pd.read_excel(
    'https://www2.census.gov/programs-surveys/popest/geographies/2020/all-geocodes-v2020.xlsx',
    header=4)
#remove dot
temp = [x.replace(".", "") for x in fips_all.iloc[:, 6]]
fips_all.iloc[:, 6] = temp
#get county code
#simplify the json object
# counties_code = []
# state_code = []
# name = []
# for x in counties['features']:
#     counties_code.append(x['properties']['COUNTY'])
#     state_code.append(x['properties']['STATE'])
#     name.append(x['properties']['NAME'])
# county_df  = pd.DataFrame({'county': counties_code, 'state': state_code, 'name': name})

fips = []
for idx, ct in pop.iterrows():
    temp = fips_all[(fips_all.iloc[:, 6] == ct['County'])
                    & (fips_all.iloc[:, 1] == ct['State_code'])]
    if len(temp) > 0:
        fips.append(temp.iloc[0, 2])
    else:
        fips.append(0)
    #fips.append(county_df[(county_df['name'] == ct['County'].split(" ")[0]) & (county_df['state'] == ct['State_code'])]['county'].to_string(index=False))

pop['county_code'] = fips
#manually change DC
pop.iloc[pop[pop['County'] == 'District of Columbia'].index, 10] = 1

# convert STATE+COUNTY into fips code
fips = []
for idx, ct in pop.iterrows():
    fips.append(
        str(ct['State_code']).zfill(2) + str(ct['county_code']).zfill(3))

pop['fips'] = fips
pop['percent'] = pop['tot_change'] / pop['tot_pop']
pop['log_change'] = [np.sign(x) * np.log(abs(x)) for x in pop['tot_change']]

#plotting...
txt = [-100000, -100, 1, 100, 100000]
vals = [np.sign(x) * np.log(abs(x)) for x in txt]

pop['log_pop'] = [np.log(x) for x in pop['tot_pop']]
pop['domestic_percentage'] = pop['Domestic'] / pop['tot_pop']
pop['domestic_log'] = [np.sign(x) * np.log(abs(x)) for x in pop['Domestic']]
#scatterplot
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots()
sns.scatterplot(data=pop, x="log_pop", y="domestic_log")
plt.show()

fig = px.choropleth_mapbox(pop,
                           geojson=counties,
                           locations='fips',
                           color='domestic_log',
                           hover_name='County',
                           hover_data={
                               'fips': False,
                               'log_change': False,
                               'tot_pop': ':,',
                               'percent': ':.2%'
                           },
                           color_continuous_scale="balance",
                           center={
                               "lat": 37.0902,
                               "lon": -95.7129
                           },
                           mapbox_style="open-street-map",
                           color_continuous_midpoint=0,
                           opacity=0.5,
                           zoom=4,
                           labels={
                               'tot_pop': 'Total Population',
                               'percent': 'Percent Changed'
                           })

fig.layout.coloraxis.colorbar = dict(title='Population Change',
                                     tickvals=vals,
                                     ticktext=txt,
                                     tickformat='","')
fig.show()

pop['new'] = [np.log(x + 655400) for x in pop['Domestic']]

fig = px.scatter(pop,
                 x="log_pop",
                 y="new",
                 hover_name='County',
                 hover_data={
                     'State': True,
                     'tot_pop': ":,",
                     'log_pop': False
                 })
fig.show()

from sklearn.linear_model import LinearRegression

X = np.array(pop['log_pop']).reshape(-1, 1)
y = pop['new']
reg = LinearRegression().fit(X, y)

residuals = y - reg.predict(X)

res_mean = residuals.mean()
res_sd = residuals.std()

pop['residuals'] = [(x - res_mean) / res_sd for x in residuals]

fig = px.scatter(pop,
                 x="log_pop",
                 y="residuals",
                 hover_name='County',
                 hover_data={
                     'State': True,
                     'tot_pop': ":,",
                     'log_pop': False
                 })
fig.show()

fig = px.choropleth_mapbox(pop,
                           geojson=counties,
                           locations='fips',
                           color='residuals',
                           hover_name='County',
                           hover_data={
                               'fips': False,
                               'log_change': False,
                               'tot_pop': ':,',
                               'percent': ':.2%'
                           },
                           range_color=[-1, 1],
                           color_continuous_scale="balance",
                           center={
                               "lat": 37.0902,
                               "lon": -95.7129
                           },
                           mapbox_style="open-street-map",
                           color_continuous_midpoint=0,
                           opacity=0.5,
                           zoom=4,
                           labels={
                               'tot_pop': 'Total Population',
                               'percent': 'Percent Changed'
                           })
fig.show()

pop[pop['log_change'] < 0]

fig.write_image("pop_change.png")
fig.write_html("pop_change.html")

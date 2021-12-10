from icoscp.sparql.runsparql import RunSparql
import ipywidgets as widgets
from IPython.display import display


def query_stations():
    query = \
        f'prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>\n' + \
        f'prefix prov: <http://www.w3.org/ns/prov#>\n' + \
        f'select ?dobj ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd\n' + \
        f'where {{\n' + \
        f'	VALUES ?spec {{<http://meta.icos-cp.eu/resources/cpmeta/atcMtoL2DataObject>}}\n' + \
        f'	?dobj cpmeta:hasObjectSpec ?spec .\n' + \
        f'	?dobj cpmeta:hasSizeInBytes ?size .\n' + \
        f'?dobj cpmeta:hasName ?fileName .\n' + \
        f'?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .\n' + \
        f'?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .\n' + \
        f'?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .\n' + \
        f'	FILTER NOT EXISTS {{[] cpmeta:isNextVersionOf ?dobj}}\n' + \
        f'	{{\n' + \
        f'		{{FILTER NOT EXISTS {{?dobj cpmeta:hasVariableName ?varName}}}}\n' + \
        f'		UNION\n' + \
        f'		{{\n' + \
        f'			?dobj cpmeta:hasVariableName ?varName\n' + \
        f'			FILTER (?varName = "WD" || ?varName = "WS")\n' + \
        f'		}}\n' + \
        f'	}}\n' + \
        f'}}\n' + \
        f'order by desc(?submTime)\n'
    return RunSparql(sparql_query=query, output_format='pandas').run()


def init():
    df_1 = query_stations()
    station_names = sorted(list(set(df_1['fileName'].str[22:25])))
    my_drop_down = widgets.Dropdown(options=station_names)
    display(my_drop_down)

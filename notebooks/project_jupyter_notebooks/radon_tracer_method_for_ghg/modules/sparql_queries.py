def q_find_data_object_from_name(file_name: str = None) -> str:
    """Costruct a query to find a data object id."""
    query = str()
    if file_name is None:
        raise Exception('file_name argument cannot be a None value.')
    else:
        query = '''
            prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
            select ?dobj 
            where{
                ?dobj cpmeta:hasName "''' + file_name + '''"^^xsd:string .
                FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
                FILTER EXISTS {?dobj cpmeta:hasSizeInBytes ?size }
            }
        '''
    return query


def q_find_radon_maps():
    """Construct a query to find all radon flux maps."""
    query = '''
        prefix cpmeta: <http://meta.icos-cp.eu/ontologies/cpmeta/>
        prefix prov: <http://www.w3.org/ns/prov#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>
        select ?dobj ?hasNextVersion ?spec ?fileName ?size ?submTime ?timeStart ?timeEnd
        where {
            VALUES ?spec {<http://meta.icos-cp.eu/resources/cpmeta/radonFluxSpatialL3>}
            ?dobj cpmeta:hasObjectSpec ?spec .
            BIND(EXISTS{[] cpmeta:isNextVersionOf ?dobj} AS ?hasNextVersion)
            ?dobj cpmeta:hasSizeInBytes ?size .
            ?dobj cpmeta:hasName ?fileName .
            ?dobj cpmeta:wasSubmittedBy/prov:endedAtTime ?submTime .
            ?dobj cpmeta:hasStartTime | (cpmeta:wasAcquiredBy / prov:startedAtTime) ?timeStart .
            ?dobj cpmeta:hasEndTime | (cpmeta:wasAcquiredBy / prov:endedAtTime) ?timeEnd .
            FILTER NOT EXISTS {[] cpmeta:isNextVersionOf ?dobj}
            VALUES ?keyword {"traceRadon"^^xsd:string}
            ?dobj cpmeta:hasKeyword ?keyword
        }
    '''
    return query
from SPARQLWrapper import SPARQLWrapper, JSON
#%%

CHEMBL_ENDPOINT = 'https://www.ebi.ac.uk/rdf/services/sparql'
HOMOLOGENE_ENDPOINT = 'http://homologene.bio2rdf.org/sparql'
AFFYMETRIX_ENDPOINT = 'http://affymetrix.bio2rdf.org/sparql'
CHEMBL_NAMESPACE = 'http://rdf.ebi.ac.uk/terms/chembl#'
HOMOLOGENE_NAMESPACE = 'http://bio2rdf.org/homologene:'
AFFYMETRIX_NAMESPACE = 'http://bio2rdf.org/affymetrix:'

# language=RegExp
uri_regex = r'^https?://(.*)(?<=[#/:])[^[/#:]]+$'
# language=RegExp
domain_regex = r'^(https?://[^/]+/(?:[^/]+/)?).*'

# language=RegExp
chembl_regex = r'^(.*)(?<=[#/])[^/|#]+$'
# #%% CHEMBL investigation
# sparql = SPARQLWrapper(CHEMBL_ENDPOINT)
#
# # language=sparql
# uri_query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX owl: <http://www.w3.org/2002/07/owl#>
# SELECT DISTINCT ?typestr
# WHERE {{
#     ?s rdfs:subClassOf ?type .
#     BIND (replace(str(?type), "{uri_regex}", "$1") as ?typestr) .
#     FILTER strStarts(str(?s), "{CHEMBL_NAMESPACE}") .
# }}
# """
#
# sparql.setQuery(uri_query)
# sparql.setReturnFormat(JSON)
# results = sparql.query().convert()
# #%% HOMOLOGENE investigation
# sparql = SPARQLWrapper(HOMOLOGENE_ENDPOINT)
#
#
# # language=sparql
# uri_query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX owl: <http://www.w3.org/2002/07/owl#>
# SELECT DISTINCT ?typestr
# WHERE {{
#     {{
#         ?s owl:sameAs|owl:equivalentClass ?type .
# #        ?s ?p ?type . # this results in gateway time-out error
#         BIND (replace(str(?type), "{domain_regex}", "$1") as ?typestr) .
#         FILTER (
#             strStarts(str(?s), "http://bio2rdf.org/") &&
#             regex(str(?type), "^(?!http://bio2rdf.org/).*")) .
#     }}
# }}
# LIMIT 25
# """
# sparql.setTimeout(120)
# sparql.setQuery(uri_query)
# sparql.setReturnFormat(JSON)
# results = sparql.query().convert()
#%% Affymetrix investigation
sparql = SPARQLWrapper(AFFYMETRIX_ENDPOINT)


# language=sparql
uri_query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?typestr
WHERE {{ 
    {{
        ?s owl:sameAs|owl:equivalentClass ?type .
#        ?s ?p ?type . # this results in gateway time-out error
        BIND (replace(str(?type), "{domain_regex}", "$1") as ?typestr) .
        FILTER (
            strStarts(str(?s), "http://bio2rdf.org/") && 
            regex(str(?type), "^(?!http://bio2rdf.org/).*")) .
    }}
}}
LIMIT 25
"""
sparql.setTimeout(300)
sparql.setQuery(uri_query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
#%%

asdf = results.convert()

# language=sparql
same_as_query = f"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX dbpedia2: <http://dbpedia.org/property/>
PREFIX dbpedia: <http://dbpedia.org/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX cco: <http://rdf.ebi.ac.uk/terms/chembl#>
SELECT DISTINCT ?typestr
WHERE {{
    [] a ?type .
    bind(replace(str(?type), "{uri_regex}", "$1") as ?typestr)
}}
"""

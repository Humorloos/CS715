#%%

import json
import re
import sys
import urllib.parse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rdflib
import requests
from SPARQLWrapper import SPARQLWrapper, XML
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError
from rdflib import Graph
from rdflib.plugin import register, Parser

from constants import LIFE_SCIENCES_TARGET_DIR
from utils import load_metadata_json

#%%

DUMP_DATE = '2021-08-14'
target_dir = LIFE_SCIENCES_TARGET_DIR

#%%

lod_data = {k: v for k, v in load_metadata_json(DUMP_DATE).items() if v['domain'] == 'life_sciences'}

lod_data = {k: lod_data[k] for k in list(lod_data)[:50]}

#%%

### Identify the different Media Types used within the LOD Cloud dataset metadata

register('rdfa', Parser, 'rdflib.plugins.parsers.rdfa', 'RDFaParser')

rdfaCounter = 0
counter = 0


# Different Media Types Used
def __extractMediaType(item):
    global rdfaCounter
    global counter
    mtype = item["media_type"]
    if (";" in mtype):
        mtype = mtype[:mtype.find(';')]
    mtype = str(mtype)
    if mtype == "text/html":
        if "access_url" in item:
            try:
                h = requests.get(str(item["access_url"]).strip(), timeout=10)
                if h.status_code > 399:
                    g = Graph()
                    g.parse(str(item["access_url"]).strip(), 'rdfa')
                    if (len(g) > 1):
                        rdfaCounter = rdfaCounter + 1
            except:
                pass
    if (len(mtype) == 0):
        mtype = "None"
    if (mtype in mediaTypes):
        mediaTypes[mtype] = mediaTypes[mtype] + 1
    else:
        mediaTypes[mtype] = 1


mediaTypes = dict({})
# Get Different Media Types
for key in lod_data:
    full_download = lod_data[key]["full_download"]
    other_download = lod_data[key]["other_download"]

    if (len(full_download) > 0):
        for item in full_download:
            if ("media_type" in item):
                __extractMediaType(item)
    if (len(other_download) > 0):
        for item in other_download:
            if ("media_type" in item):
                __extractMediaType(item)

# Create Chart
toPlot = {"Others": 0}

for (k, v) in mediaTypes.items():
    if k == "text/html":
        #         skip text/html as it would be large to print
        continue
    if v > 25:
        toPlot[k] = v
    else:
        toPlot["Others"] = toPlot["Others"] + 1

# Display Table
print("\033[4mTabular View\033[0m")
print("")
print("")
toPlot["text/html"] = mediaTypes["text/html"]
sorted_toPlot = sorted(toPlot.items(), key=lambda kv: kv[1])
print("{:<50} {:<10}".format('\033[1m' + 'Media Type', 'Frequency' + '\033[0m'))
for k, v in sorted_toPlot:
    print("{:<50} {:<10}".format(k, v))

print("Total text/html in RDFa: " + str(rdfaCounter))
pd.DataFrame(sorted_toPlot).set_index(0).to_csv(target_dir.joinpath('media_types.csv'))

#%%

# Identify the Dataset's Accessibility based on the LOD Cloud available metadata

acceptable_media_types = set()
acceptable_media_types.add("application/x-ntriples")
acceptable_media_types.add("application/rdf+xml")
acceptable_media_types.add("text/turtle")
acceptable_media_types.add("application/x-nquads")
acceptable_media_types.add("application/trig")
acceptable_media_types.add("application/n-triples")
acceptable_media_types.add("gzip:ntriples")
acceptable_media_types.add("application/x-gzip")
acceptable_media_types.add("application/octet-stream")
acceptable_media_types.add("application/x-ntriples")
acceptable_media_types.add("RDF")
acceptable_media_types.add("plain/text")


#%%


def __query_endpoint(uri):
    try:
        sparql_query = SPARQLWrapper(uri)
        sparql_query.setQuery('ASK {?s ?p ?o}')
        sparql_query.setReturnFormat(XML)
        sparql_query.setTimeout(3)
        results = sparql_query.query().convert()
        for _ in results.getElementsByTagName('boolean'):
            return True
        return False
    except (EndPointInternalError, AttributeError):
        try:
            params = urllib.parse.urlencode({'query': 'ASK {?s ?p ?o}'})
            results = requests.get(f'{uri}?{params}', headers={'Accept': 'application/sparql-results+json'},
                                   timeout=3).json()
            if results['boolean'] is not None:
                return True
            else:
                return False
        except:
            try:
                params = urllib.parse.urlencode({'query': 'ASK {?s ?p ?o}'})
                data = requests.get(f'{uri}?{params}', timeout=3).text
                if data:
                    return True
                else:
                    return False
            except:
                e = sys.exc_info()[0]
                return False
    except:
        e = sys.exc_info()[0]
        return False


#%%

def __query_void(voidurl):
    if __checkstatus(voidurl):
        try:
            graph = rdflib.Graph()
            graph.parse(voidurl)
            accessible = False

            result = graph.query('ASK { ?s a <http://rdfs.org/ns/void#Dataset> . }')
            for row in result:
                accessible = bool(row)

            return accessible
        except:
            e = sys.exc_info()[0]
            return False
    else:
        return False


#%%

def __checkstatus(host):
    try:
        h = requests.get(host, timeout=10)
        if h.status_code > 399:
            return False
    except:
        return False
    return True


#%%

def availableSPARQLEntryPoint(record):
    if "sparql" in record:
        if len(record["sparql"]) >= 1:
            sparqlEndpoint = record["sparql"][0]["access_url"]

            if not ("FAIL" in record["sparql"][0]["status"]):
                if __checkstatus(sparqlEndpoint):
                    return __query_endpoint(sparqlEndpoint)
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False


def availableDatadumpEntryPoint(record):
    datadumpLocation = []
    _full_download = record["full_download"]
    _other_download = record["other_download"]
    if (len(_full_download) > 0):
        for item in _full_download:
            if ("media_type" in item):
                mtype = item["media_type"]
                if (";" in mtype):
                    mtype = mtype[:mtype.find(';')]
                if (item["media_type"] in acceptable_media_types):
                    if (not (".well-known/" in item["download_url"])):
                        if (__checkstatus(item["download_url"])):
                            datadumpLocation.append(item["download_url"])
    elif (len(_other_download) > 0):
        for item in _other_download:
            if (not (".well-known/" in item["access_url"])):
                if (item["media_type"] in acceptable_media_types):
                    if (__checkstatus(item["access_url"])):
                        datadumpLocation.append(item["access_url"])

    return len(datadumpLocation) > 0


def availableVoidEntryPoint(record):
    voidLocation = []
    full_download = record["full_download"]
    other_download = record["other_download"]
    if (len(full_download) > 0):
        for item in full_download:
            if ("media_type" in item):
                mtype = item["media_type"]
                if (";" in mtype):
                    mtype = mtype[:mtype.find(';')]
                if (item["media_type"] == "meta/void"):
                    if (__checkstatus(item["download_url"])):
                        voidLocation.append(item["download_url"])
                elif (".well-known/" in item["download_url"]):
                    if (__checkstatus(item["download_url"])):
                        voidLocation.append(item["download_url"])

    elif (len(other_download) > 0):
        for item in other_download:
            if (item["media_type"] == "meta/void"):
                if (__checkstatus(item["access_url"])):
                    voidLocation.append(item["access_url"])
            elif (".well-known/" in item["access_url"]):
                voidLocation.append(item["access_url"])

    return len(voidLocation) > 0


dataSources = dict({})  # key, (dd,sparql,void) 1 = available 0 = not available
for key in lod_data:
    dataSources[key] = (availableDatadumpEntryPoint(lod_data[key]), availableSPARQLEntryPoint(lod_data[key]),
                        availableVoidEntryPoint(lod_data[key]))
pd.DataFrame(dataSources, index=['Datadump', 'SPARQL', 'voID']).T.to_csv(target_dir.joinpath('accessibility.csv'))
#%%

# The next snippet checks the number of datasets that have no access point
noAccessPoint = 0

for key in lod_data:
    full_download = lod_data[key]["full_download"]
    other_download = lod_data[key]["other_download"]
    sparql = lod_data[key]["sparql"]

    if ((len(full_download) == 0) and (len(other_download) == 0) and (len(sparql) == 0)):
        noAccessPoint = noAccessPoint + 1

print("Number of datasets without an access point: " + str(noAccessPoint))

#%% md

# This snippet will create a JSON file that can be used to recreate the LOD cloud visualisation.The LOD cloud diagram
# code can be found here: https://github.com/lod-cloud/lod-cloud-draw

#%%
available_lod_data = lod_data.copy()

modified_dataSources = dict(dataSources)
for (k, v) in dataSources.items():
    if v == (0, 0, 0):
        del modified_dataSources[k]
        del available_lod_data[k]

print(json.dumps(available_lod_data))

with open(target_dir.joinpath('available_lod_data.json'), 'w') as out_file:
    json.dump(available_lod_data, out_file)


#%% md

# The following code snippet will identify the different access points of datasets

#%%

dd = 0
sparql = 0
void = 0
ddSparql = 0
ddVoid = 0
SparqlVoid = 0
allthree = 0
nothing = 0
for (k, v) in dataSources.items():
    if v == (0, 0, 0):
        nothing += 1
    if v == (1, 0, 0):
        dd += 1
    if v == (0, 1, 0):
        sparql += 1
    if v == (0, 0, 1):
        void += 1
    if v == (1, 1, 0):
        ddSparql += 1
    if v == (1, 0, 1):
        ddVoid += 1
    if v == (0, 1, 1):
        SparqlVoid += 1
    if v == (1, 1, 1):
        allthree += 1

print("Only Datadump: " + str(dd))
print("Only SPARQL: " + str(sparql))
print("Only VOID: " + str(void))
print("Only Datadump and SPARQL: " + str(ddSparql))
print("Only Datadump and VOID: " + str(ddVoid))
print("Only SPARQL and VOID: " + str(SparqlVoid))
print("All three entry points: " + str(allthree))
print("No entry points: " + str(nothing))

labels = 'Datadump', 'SPARQL', 'voID', 'More than 1\nDiscoverability\nEntry', 'None'
sizes = [dd, sparql, void, (ddSparql + ddVoid + SparqlVoid + allthree), nothing]

fig, ax = plt.subplots(figsize=(7, 7))
patches, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=False, startangle=90,
                                   textprops={'fontsize': 12})
texts[0].set_fontsize(15)
texts[1].set_fontsize(15)
texts[2].set_fontsize(15)
texts[3].set_fontsize(15)
texts[4].set_fontsize(15)

ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

plt.savefig(target_dir.joinpath('accessibility.png'), bbox_inches="tight")

plt.show()

#%%

# Identifying Licenses

# Licences are the heart of Open Data.They define whether third parties can re - use data or otherwise, and to what
# extent.For this experiment we parsed through each dataset in the data file and looked for the value attributed to the
# `license` key.

# The next code snippet parses through the LOD Cloud data and checks the license for each dataset.The variable
# `licensesUsed` stores all licenses used and their frequency.
licensesUsed = dict({})
for key in lod_data:
    if "license" in lod_data[key]:
        theLicence = lod_data[key]["license"]
        if theLicence == "":
            continue
        if not (theLicence in licensesUsed):
            licensesUsed[theLicence] = 1
        else:
            licensesUsed[theLicence] = licensesUsed[theLicence] + 1


#%% md

# Visualising the licenses used


#%%

# Class used to visualse the data
def visualiseLicenseData(licenses_used):
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.barh(range(len(licenses_used)), licenses_used.values(), height=0.5)
    ax.set_yticks(np.arange(len(licenses_used.keys())))
    ax.set_yticklabels(licenses_used.keys(), fontsize=12, fontweight='bold')
    ax.invert_yaxis()
    plt.xlabel("Frequency", fontsize=15, fontweight='bold')

    for i, v in enumerate(licenses_used.values()):
        ax.text(v + 2, i + 0.08, str(v), color='black', fontweight='bold', fontsize=10)

    # Display Table
    print("\033[4mTabular View\033[0m")
    print("")
    print("")
    sorted_licensesUsed = sorted(licenses_used.items(), key=lambda kv: kv[1])
    print("{:<60} {:<40} {:<10}".format('\033[1m' + 'License', 'Frequency', 'Percentage' + '\033[0m'))
    totalItems = len(lod_data)
    for k, v in sorted_licensesUsed:
        print("{:<60} {:<40} {:<10}".format(k, v, str((v * 100.0) / totalItems) + "%"))

    # Display Plot
    print("")
    print("")
    print("\033[4mBar View\033[0m")
    plt.savefig(target_dir.joinpath('licenses.png'), bbox_inches="tight")
    plt.show()


#%%

# Visualise all data
visualiseLicenseData(licensesUsed)

#%%

# Visualise Summarised Data
licenseLabels = dict({})

licenseLabels['https://creativecommons.org/licenses/by/3.0/'] = "CC-BY-3.0"
licenseLabels['http://reference.data.gov.uk/id/open-government-licence'] = "OGL-UK"
licenseLabels['http://www.opendefinition.org/licenses/odc-by'] = "ODC-BY"
licenseLabels['http://www.opendefinition.org/licenses/odc-pddl'] = "ODC-PDDL"
licenseLabels['http://www.opendefinition.org/licenses/odc-odbl'] = "ODC-ODBL"
licenseLabels['http://creativecommons.org/licenses/by-nc/2.0/'] = "CC-BY-NC-2.0"
licenseLabels['http://www.opendefinition.org/licenses/cc-zero'] = "CC0"
licenseLabels['http://www.opendefinition.org/licenses/cc-by-sa'] = "CC-BY-SA"
licenseLabels['http://www.opendefinition.org/licenses/cc-by'] = "CC-BY"

summLicensesUsed = dict({})
summLicensesUsed['Other'] = 0
for k, v in licensesUsed.items():
    if (v < 10):
        summLicensesUsed['Other'] = summLicensesUsed['Other'] + v
    else:
        if k in licenseLabels:
            summLicensesUsed[licenseLabels[k]] = v

visualiseLicenseData(summLicensesUsed)


#%%

# In the next experiment, we use a regular expression to identify the dataset which potentially have a license assigned
# to its description


def __tryDecoding(text):
    try:
        text = str(text, 'utf-8')
        return text
    except TypeError:
        return text


def __licenseStringExtractor(text):
    potentialText = __tryDecoding(text)

    if (potentialText):
        str_list = potentialText.splitlines()
        str_list = filter(None, str_list)
        new_desc = ' '.join([__tryDecoding(x) for x in str_list])

        p = re.compile(r'.*(licensed?|copyrighte?d?).*(under|grante?d?|rights?).*', re.IGNORECASE | re.MULTILINE)

        m = p.match(new_desc)

        return not (m == None)
    else:
        return False


potentialLicence = []
for key in lod_data:
    if ("description" in lod_data[key]):
        text = lod_data[key]["description"]['en']
        if (__licenseStringExtractor(text)):
            potentialLicence.append(str(key))

print(potentialLicence)

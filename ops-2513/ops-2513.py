import requests
import networkx as nx
import base64
import yaml
import matplotlib.pyplot as plt

headers = {}
rapids_repos = ['rmm', 'dask-cuda', 'cucim', 'cusignal', 'ucx-py', 'raft', 'cudf', 'cumlprims_mg', 'cuspatial', 'cugraph-ops', 'cuml', 'cugraph', 'cuxfilter']
response_ = None

def parse_nightly_workflow(repo_name):
    global response_
    if response_ is None:
        url = f"https://api.github.com/repos/rapidsai/actions/contents/.github/workflows/nightly-pipeline.yaml"
        response = requests.get(url, headers=headers)
        response_ = response
    content = response_.json().get("content")
    decoded_content = base64.b64decode(content).decode("utf-8")
    parsed_yaml = yaml.safe_load(decoded_content)
    repo_job = parsed_yaml.get("jobs", {}).get(repo_name+"-build", None)
    
    if repo_job is None:
        return []
    needs = repo_job.get("needs")
    if isinstance(needs, str): 
        needs = [needs]
    needs = list(filter(lambda x: "-build" in x, needs))
    needs = list(map(lambda dep: dep.split("-build")[0], needs))
    return needs

# Build dependency graph
dependency_graph = nx.DiGraph()
for repo in rapids_repos:
    # for repo in group:
    dependency_graph.add_node(repo)
    dependencies = parse_nightly_workflow(repo)
    for dep_name in dependencies:
        if dep_name in dependency_graph.nodes:
            dependency_graph.add_edge(dep_name, repo)

print()
# Text-based visualization of the graph
for node in dependency_graph.nodes:
    neighbors = list(dependency_graph.successors(node))
    if neighbors:
        print(f"{node} <- {', '.join(neighbors)}")
    else:
        print(node)
print()


# Sort repositories by dependency order
sorted_repos = list(nx.topological_sort(dependency_graph))

padded = [None] * (len(sorted_repos)+4)
i,j=0,0
while i<len(sorted_repos) and j<len(padded):
    if sorted_repos[i] not in ["cusignal", "cudf", "cugraph", "cuxfilter"]:
        padded[j] = sorted_repos[i]
    else:
        if sorted_repos[i] == "cusignal":
            padded[j+1] = "kvikio"
        if sorted_repos[i] == "cudf":
            padded[j+1] = "xgboost"
        if sorted_repos[i] == "cugraph":
            padded[j+1] = "clx"
        if sorted_repos[i] == "cuxfilter":
            padded[j+1] = "integration"
        padded[j] = sorted_repos[i]
        j+=1  
    j+=1
    i+=1

print("This is the build order (sorted by the order of dependency):\n", "\n ".join(sorted_repos))
print()
print("This is the sorted build order (adjusted to include the libraries not present in the nightly workflow):\n", "\n ".join(padded))

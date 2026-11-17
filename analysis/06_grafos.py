"""Semana 13 - Minería de grafos: red de co-compra de categorías y comunidades (NetworkX)."""
from pathlib import Path
from itertools import combinations
from collections import Counter
import pandas as pd, networkx as nx
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"analysis"/"outputs_s13"
b=pd.read_csv(ROOT/"data/processed/canastas_items.csv").merge(pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv",usecols=["order_id","customer_unique_id"]),on="order_id")
basket=b.groupby("customer_unique_id").categoria.apply(lambda s:sorted(set(s)))
cnt=Counter(); w=Counter()
for cats in basket:
    for c in cats: cnt[c]+=1
    for a,c in combinations(cats,2): w[(a,c)]+=1
G=nx.Graph()
for c,n in cnt.items(): G.add_node(c,clientes=n)
for (a,c),n in w.items():
    if n>=3: G.add_edge(a,c,weight=n)
G.remove_nodes_from([n for n in list(G) if G.degree(n)==0])
print("nodos",G.number_of_nodes(),"aristas",G.number_of_edges(),"densidad",round(nx.density(G),3))
comm=list(nx.community.greedy_modularity_communities(G,weight="weight")); mod=nx.community.modularity(G,comm,weight="weight")
cid={n:i for i,cs in enumerate(comm) for n in cs}
deg=dict(G.degree(weight="weight")); bc=nx.betweenness_centrality(G,weight=None); pr=nx.pagerank(G,weight="weight")
nodes=pd.DataFrame([dict(categoria=n,comunidad=cid[n],clientes=G.nodes[n]["clientes"],grado=G.degree(n),fuerza=deg[n],intermediacion=bc[n],pagerank=pr[n]) for n in G]).sort_values("pagerank",ascending=False)
nodes.to_csv(OUT/"11_grafo_nodos.csv",index=False)
edges=pd.DataFrame([dict(origen=a,destino=c,clientes_en_comun=d["weight"]) for a,c,d in G.edges(data=True)]).sort_values("clientes_en_comun",ascending=False)
edges.to_csv(OUT/"12_grafo_aristas.csv",index=False)
print("modularidad",round(mod,3),"| comunidades",len(comm),[len(c) for c in comm])
for i,cs in enumerate(comm): print(i,sorted(cs,key=lambda x:-cnt[x])[:6])
print(nodes.head(8).round(3).to_string(index=False)); print(edges.head(10).to_string(index=False))
pd.DataFrame([dict(nodos=G.number_of_nodes(),aristas=G.number_of_edges(),densidad=nx.density(G),modularidad=mod,comunidades=len(comm),componentes=nx.number_connected_components(G))]).to_csv(OUT/"13_grafo_resumen.csv",index=False)

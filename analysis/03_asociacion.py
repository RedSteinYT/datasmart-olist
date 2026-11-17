"""Semana 10 - Reglas de asociación: Apriori, FP-Growth y ECLAT (implementación propia, sin mlxtend)."""
from pathlib import Path
from itertools import combinations
from collections import defaultdict
import time, pandas as pd

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT/"analysis"/"outputs_s10"
b = pd.read_csv(ROOT/"data/processed/canastas_items.csv")
cu = pd.read_csv(ROOT/"data/processed/pedidos_procesados.csv", usecols=["order_id","customer_unique_id"])
b = b.merge(cu, on="order_id")
# Canasta = categorías distintas compradas por un cliente único (histórico). Solo canastas con >=2 categorías.
T_all = b.groupby("customer_unique_id").categoria.apply(lambda s: frozenset(s)).tolist()
T = [t for t in T_all if len(t) >= 2]
N = len(T); MINSUP = 0.004; MINCONF = 0.05; MAXLEN = 3
print("clientes totales:", len(T_all), "| canastas con >=2 categorías:", N)

def apriori(T, minsup, maxlen):
    n=len(T); cnt=defaultdict(int)
    for t in T:
        for i in t: cnt[frozenset([i])]+=1
    cur={k:v for k,v in cnt.items() if v/n>=minsup}; freq=dict(cur); k=2
    while cur and k<=maxlen:
        items=sorted({i for s in cur for i in s}); cand=set()
        keys=list(cur)
        for a,c in combinations(keys,2):
            u=a|c
            if len(u)==k and all(frozenset(x) in cur for x in combinations(u,k-1)): cand.add(u)
        cnt=defaultdict(int)
        for t in T:
            for c in cand:
                if c<=t: cnt[c]+=1
        cur={c:v for c,v in cnt.items() if v/n>=minsup}; freq.update(cur); k+=1
    return freq

class Node:
    __slots__=("item","count","parent","children","link")
    def __init__(s,item,parent): s.item=item;s.count=0;s.parent=parent;s.children={};s.link=None
def fpgrowth(T, minsup, maxlen):
    n=len(T); minc=minsup*n; c1=defaultdict(int)
    for t in T:
        for i in t: c1[i]+=1
    c1={i:v for i,v in c1.items() if v>=minc}
    def build(trans):  # trans: list of (items, count)
        root=Node(None,None); header={}
        for items,c in trans:
            node=root
            for i in items:
                ch=node.children.get(i)
                if ch is None:
                    ch=Node(i,node); node.children[i]=ch
                    ch.link=header.get(i); header[i]=ch
                ch.count+=c; node=ch
        return header
    rank={i:r for r,i in enumerate(sorted(c1,key=lambda x:(-c1[x],x)))}
    order=lambda t:sorted([i for i in t if i in c1],key=lambda x:rank[x])
    freq={}
    def mine(header,suffix):
        for item in sorted(header, key=lambda i: -rank[i]):
            node=header[item]; total=0; paths=[]
            while node is not None:
                total+=node.count; p=[]; q=node.parent
                while q.item is not None: p.append(q.item); q=q.parent
                if p: paths.append((p[::-1],node.count))
                node=node.link
            if total<minc: continue
            new=suffix|{item}; freq[frozenset(new)]=total
            if len(new)<maxlen and paths:
                cc=defaultdict(int)
                for p,c in paths:
                    for i in p: cc[i]+=c
                keep={i for i,v in cc.items() if v>=minc}
                trans=[([i for i in p if i in keep],c) for p,c in paths]
                h=build(trans)
                if h: mine(h,new)
    mine(build([(order(t),1) for t in T]),frozenset())
    return freq

def eclat(T, minsup, maxlen):
    n=len(T); minc=minsup*n; tid=defaultdict(set)
    for idx,t in enumerate(T):
        for i in t: tid[i].add(idx)
    freq={}
    def rec(prefix,cands):
        for k,(item,ids) in enumerate(cands):
            new=prefix|{item}; freq[frozenset(new)]=len(ids)
            if len(new)<maxlen:
                nxt=[(j,ids&ids2) for j,ids2 in cands[k+1:]]
                nxt=[(j,s) for j,s in nxt if len(s)>=minc]
                if nxt: rec(new,nxt)
    base=sorted([(i,s) for i,s in tid.items() if len(s)>=minc], key=lambda x:(len(x[1]),x[0]))
    rec(frozenset(),base); return freq

def rules(freq, n, minconf):
    out=[]
    for s,c in freq.items():
        if len(s)<2: continue
        for r in range(1,len(s)):
            for a in combinations(sorted(s),r):
                a=frozenset(a); cons=s-a
                if a not in freq or cons not in freq: continue
                conf=c/freq[a]; lift=conf/(freq[cons]/n)
                if conf>=minconf: out.append(dict(antecedente=", ".join(sorted(a)),consecuente=", ".join(sorted(cons)),
                    support=c/n,confidence=conf,lift=lift,n_clientes=c))
    return pd.DataFrame(out).sort_values(["lift","support"],ascending=False)

res=[]; store={}
for name,fn in [("Apriori",apriori),("FP-Growth",fpgrowth),("ECLAT",eclat)]:
    t0=time.perf_counter(); f=fn(T,MINSUP,MAXLEN); dt=time.perf_counter()-t0
    store[name]=f; r=rules(f,N,MINCONF)
    res.append(dict(algoritmo=name,itemsets_frecuentes=len(f),reglas=len(r),tiempo_s=round(dt,3)))
    r.to_csv(OUT/f"02_reglas_{name.lower().replace('-','')}.csv",index=False)
comp=pd.DataFrame(res); same=(set(store["Apriori"])==set(store["FP-Growth"])==set(store["ECLAT"]))
print(comp.to_string(index=False)); print("¿Mismos itemsets en los 3?:", same)
comp.to_csv(OUT/"03_comparacion_algoritmos.csv",index=False)
r=pd.read_csv(OUT/"02_reglas_fpgrowth.csv"); r=r[r.n_clientes>=10]
print(r.head(15).to_string(index=False))
r.head(30).to_csv(OUT/"04_top_reglas.csv",index=False)
pd.DataFrame([dict(clientes_totales=len(T_all),canastas_multicategoria=N,min_support=MINSUP,min_confidence=MINCONF,max_len=MAXLEN,mismos_itemsets=same)]).to_csv(OUT/"05_parametros_asociacion.csv",index=False)

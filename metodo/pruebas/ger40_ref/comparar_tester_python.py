import re, html, pandas as pd, numpy as np
t=open('ger.html').read()
num=lambda x: float(x.replace(' ','')) if x else np.nan
rows=[[html.unescape(re.sub(r'<[^>]+>','',c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>',tr,flags=re.S)] for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',t,flags=re.S)]
sl={};out=[];cur=None
for r in rows:
    if len(r)==11 and r[2]=='GER40.cash' and r[10].startswith('ORB'): sl[r[0]]=num(r[6])
    if len(r)==13 and r[2]=='GER40.cash':
        if r[4]=='in': cur=r
        else:
            e=num(cur[6]); d=1 if cur[3]=='buy' else -1; st=abs(e-sl[cur[0]])
            out.append(dict(fecha=cur[0][:10].replace('.','-'),hin=cur[0][11:16],hout=r[0][11:16],lado='LONG' if d>0 else 'SHORT',R_mt5=d*(num(r[6])-e)/st,usd=num(r[10]),swap=num(r[9]),vol=num(r[5]),stop=st,cm=r[12]))
m=pd.DataFrame(out); m.to_csv('mt5_ops.csv',index=False)
print(len(sl),len(m)); print(m.R_mt5.describe().round(3))
py=pd.read_csv('/mnt/project-files/probar-mt5/ORB_GER40_referencia_python.csv')
j=m.merge(py,on='fecha',how='outer',indicator=True); print(j._merge.value_counts())
b=j[j._merge=='both']; s=b[b.lado_x==b.lado_y]
print('lado igual %.3f n %d'%((b.lado_x==b.lado_y).mean(),len(b)))
print('medias: mt5 %.3f py %.3f | comunes mt5 %.3f py %.3f corr %.2f'%(m.R_mt5.mean(),py.R_python.mean(),b.R_mt5.mean(),b.R_python.mean(),b.R_mt5.corr(b.R_python)))
dd=s.R_mt5-s.R_python; print('dif |>0.1|: %.2f, |>0.5|: %.2f, media %.3f'%((dd.abs()>0.1).mean(),(dd.abs()>0.5).mean(),dd.mean()))
m['año']=m.fecha.str[:4]; py['año']=py.fecha.str[:4]
print(pd.concat([m.groupby('año').R_mt5.agg(['size','mean']),py.groupby('año').R_python.agg(['size','mean'])],axis=1).round(3))
print(j[j._merge!='both'][['fecha','_merge','lado_x','R_mt5','lado_y','R_python']].to_string())
x=s.assign(d=dd).sort_values('d'); print(x[['fecha','lado_x','hin','hout','R_mt5','R_python','cm']].head(8).to_string()); print(x[['fecha','lado_x','hin','hout','R_mt5','R_python','cm']].tail(8).to_string())
print('swap total',m.swap.sum(), 'usd',m.usd.sum())

"""SARIMA y Prophet para la serie diaria de ventas. NO se ejecutó en el entorno del asistente (sin statsmodels/prophet);
correr en Google Colab. Requiere: pip install statsmodels prophet. Subir antes analysis/outputs_s13/06_serie_diaria.csv."""
import pandas as pd, numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
s = pd.read_csv("06_serie_diaria.csv", parse_dates=["fecha"]).set_index("fecha").asfreq("D")
y = s.ventas; H = 30; train, test = y[:-H], y[-H:]
def m(a, p): return dict(MAE=np.mean(np.abs(a-p)), RMSE=np.sqrt(np.mean((a-p)**2)), MAPE=np.mean(np.abs(a-p)/np.maximum(a,1))*100)
res = SARIMAX(train, order=(1,1,1), seasonal_order=(1,0,1,7)).fit(disp=False)
f_sarima = res.forecast(H); print("SARIMA(1,1,1)(1,0,1,7)", m(test.values, f_sarima.values))
from prophet import Prophet
dfp = train.reset_index(); dfp.columns = ["ds","y"]
pm = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False).fit(dfp)
f_prophet = pm.predict(pm.make_future_dataframe(H))["yhat"].iloc[-H:].values; print("Prophet", m(test.values, f_prophet))
pd.DataFrame([{"modelo":"SARIMA","**":0,**m(test.values,f_sarima.values)},{"modelo":"Prophet","**":0,**m(test.values,f_prophet)}]).drop(columns="**").to_csv("07b_sarima_prophet.csv", index=False)

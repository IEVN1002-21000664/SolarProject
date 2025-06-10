from flask import Flask, request, jsonify
import pandas as pd
import math
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 
# Cargar datos una sola vez
horas_solares = pd.read_csv('Horas_solares.csv').dropna(subset=['Ciudad', 'Insolacion'])
catalogo_proveedor = pd.read_csv('Catalogo_proveedor.csv').dropna(subset=['Clave', 'Potencia', 'Ancho', 'Alto'])

@app.route("/calcular", methods=["POST"])
def calcular_paneles():
    data = request.json
    ciudad_index = int(data['ciudad_index'])
    kwh_gastados = float(data['kwh_gastados'])
    ancho = float(data['ancho'])
    alto = float(data['alto'])

    if ciudad_index < 0 or ciudad_index >= len(horas_solares):
        return jsonify({"error": "Ciudad no válida"}), 400

    ciudad = horas_solares.iloc[ciudad_index]
    insolacion = ciudad['Insolacion']
    area_azotea = ancho * alto

    factor_eficiencia = 0.85
    factor_espacio = 1.25
    angulo_radianes = math.radians(15)

    catalogo = catalogo_proveedor.copy()
    catalogo['Produccion_kWh_mensual'] = (
        (catalogo['Potencia'] / 1000) * insolacion * 30.4 * factor_eficiencia
    )

    opciones_validas = []

    for _, row in catalogo.iterrows():
        produccion = row['Produccion_kWh_mensual']
        if pd.isna(produccion) or produccion <= 0:
            continue

        cantidad = math.ceil(kwh_gastados / produccion)
        total = cantidad * produccion
        diferencia = abs(total - kwh_gastados)

        area_panel = row['Ancho'] * row['Alto'] * math.cos(angulo_radianes)
        area_total = cantidad * area_panel * factor_espacio

        if area_total <= area_azotea:
            opciones_validas.append({
                "clave": row['Clave'],
                "cantidad": cantidad,
                "produccion_total": round(total, 2),
                "diferencia": round(diferencia, 2),
                "area_usada": round(area_total, 2)
            })

    if opciones_validas:
        mejor = min(opciones_validas, key=lambda x: x['diferencia'])
        return jsonify({"mejor_opcion": mejor})
    else:
        return jsonify({"mensaje": "Ningún panel disponible se ajusta al espacio"}), 200

if __name__ == "__main__":
    app.run(debug=True)

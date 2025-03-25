import requests
import json

# Configuracion del servidor Odoo
ODOO_URL = "http://localhost:8999"
API_ENDPOINT = f"{ODOO_URL}/api/create_ticket"

# Credenciales de autenticacion
USERNAME = "admin"
PASSWORD = "1"
DB = "ATM_TEST"

# Iniciar sesion en Odoo para obtener la cookie de autenticacion
session = requests.Session()
data = {
    'db': DB,
    'login': USERNAME,
    'password': PASSWORD,
}
login_response = session.post(f"{ODOO_URL}/web/session/authenticate", json={'params': data})

if login_response.status_code == 200 and login_response.json().get("result"):  
    print("Autenticacion exitosa")
    
    # Datos del ticket a crear
    payload = {
        "ticket_service_id": 3,
        "turn_establishment_id": 1,
        'location':'location_1',
        "car_plate": "ABC-123",
        "partner_id": 4,
        "html_detail": "<p>Contenido del ticket</p>"
    }
    
    headers = {'Content-Type': 'application/json'}
    response = session.post(API_ENDPOINT, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("Respuesta del servidor:", response.json())
    else:
        print("Error en la solicitud:", response.text)
else:
    print("Error en la autenticacion:", login_response.text)

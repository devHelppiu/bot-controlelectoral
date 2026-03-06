# Bot Control Electoral — WhatsApp 🗳️

Chatbot de WhatsApp para control electoral usando Meta Cloud API, Firebase y Google Vision OCR.

## Arquitectura

```
WhatsApp (Usuario)
    ↕ Meta Cloud API
Firebase Cloud Function (webhook)
    ├── API Votantes (consulta cédula)
    ├── Google Vision (OCR carnet)
    ├── Firebase Realtime Database (registros)
    └── Firebase Storage (fotos)

Firebase Hosting → Dashboard (HTML/JS + Chart.js)
    └── Firebase Realtime Database (lectura en tiempo real)
```

## Flujo del Bot

1. **Usuario envía mensaje** → Bot saluda y solicita cédula
2. **Usuario envía cédula** → Bot consulta API de votantes, verifica duplicados
3. **Bot muestra datos** → Pide confirmación (botones Sí/No)
4. **Usuario confirma** → Bot solicita nombre del candidato
5. **Usuario escribe candidato** → Bot solicita foto del carnet electoral
6. **Usuario envía foto** → Bot verifica con OCR, guarda registro completo

## Requisitos Previos

- [Firebase CLI](https://firebase.google.com/docs/cli) instalado (`npm install -g firebase-tools`)
- Proyecto Firebase con Realtime Database, Storage y Cloud Functions habilitados
- Cuenta de [Meta WhatsApp Business](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs/setup) habilitada en el proyecto
- Python 3.11+

## Configuración

### 1. Clonar y configurar Firebase

```bash
# Iniciar sesión en Firebase
firebase login

# Configurar el proyecto
firebase use YOUR_PROJECT_ID
```

### 2. Configurar variables de entorno

Edita `.env.example` y renómbralo a `.env`, o configura los secrets de Firebase:

```bash
# Configurar secrets para Cloud Functions
firebase functions:secrets:set WHATSAPP_TOKEN
firebase functions:secrets:set WHATSAPP_PHONE_NUMBER_ID
firebase functions:secrets:set WHATSAPP_VERIFY_TOKEN
firebase functions:secrets:set VOTANTES_API_KEY
firebase functions:secrets:set FIREBASE_DATABASE_URL
firebase functions:secrets:set FIREBASE_STORAGE_BUCKET
```

### 3. Configurar dashboard

Edita `public/js/firebase-config.js` con los datos de tu proyecto Firebase.

### 4. Habilitar Google Vision API

```bash
gcloud services enable vision.googleapis.com
```

### 5. Desplegar

```bash
firebase deploy
```

### 6. Configurar Webhook en Meta

1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. En tu app → WhatsApp → Configuration
3. Callback URL: `https://us-central1-YOUR_PROJECT_ID.cloudfunctions.net/webhook`
4. Verify Token: el mismo valor de `WHATSAPP_VERIFY_TOKEN` (default: `controlelectoral2026`)
5. Suscríbete al campo `messages`

## Estructura del Proyecto

```
bot-controlelectoral/
├── functions/                    # Cloud Functions (Python)
│   ├── main.py                   # Entry point - webhook
│   ├── config.py                 # Configuración
│   ├── requirements.txt          # Dependencias Python
│   ├── whatsapp/
│   │   ├── handler.py            # Parser de mensajes
│   │   ├── sender.py             # Enviar mensajes
│   │   └── media.py              # Descargar media
│   ├── services/
│   │   ├── votantes_api.py       # Cliente API votantes
│   │   ├── firebase_db.py        # CRUD Firebase DB
│   │   ├── firebase_storage.py   # Upload a Storage
│   │   └── ocr_service.py        # Google Vision OCR
│   └── conversation/
│       └── flow.py               # Máquina de estados
├── public/                       # Dashboard (Firebase Hosting)
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js                # Lógica principal
│       ├── charts.js             # Gráficos Chart.js
│       └── firebase-config.js    # Config Firebase cliente
├── firebase.json
├── database.rules.json
├── storage.rules
└── .firebaserc
```

## Modelo de Datos (Realtime Database)

```json
{
  "registros": {
    "{cedula}": {
      "cedula": "1144070039",
      "nombre_completo": "ALVARO JOSE TORRES BARANDICA",
      "candidato": "NOMBRE DEL CANDIDATO",
      "municipio_votacion": "CALI",
      "puesto": "UNIVERSIDAD CATOLICA SEDE MELENDEZ",
      "mesa": 17,
      "foto_url": "https://storage...",
      "ocr_verificado": true,
      "fecha_registro": 1741190400000,
      "estado": "completado"
    }
  },
  "conversaciones": {
    "{telefono}": {
      "estado": "ESPERANDO_CEDULA",
      "ultima_actividad": 1741190400000
    }
  },
  "estadisticas": {
    "total_registros": 42,
    "por_candidato": {
      "CANDIDATO_X": { "nombre": "Candidato X", "count": 25 }
    }
  }
}
```

## Dashboard

El dashboard se conecta a Firebase Realtime Database y muestra:

- **Métricas**: Total registros, candidatos únicos, municipio líder, % verificados OCR
- **Gráfico de barras**: Votos por candidato
- **Gráfico de dona**: Distribución por municipio
- **Gráfico horizontal**: Top 10 puestos de votación
- **Tabla paginada**: Todos los registros con indicador OCR
- **Filtros**: Por municipio, candidato y rango de fechas

## Desarrollo Local

```bash
cd functions
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Emulador de Firebase
firebase emulators:start
```

## Licencia

Proyecto privado — Helppiu © 2026

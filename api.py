from fastapi import FastAPI
from schemas import RawTransaction
import pika, os, json
from dotenv import load_dotenv
from db import get_connection
from fastapi.middleware.cors import CORSMiddleware
import datetime
from fastapi.encoders import jsonable_encoder
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["http://localhost:5173"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


rabbit_host = os.getenv("RABBITMQ_HOST")
rabbit_port = int(os.getenv("RABBITMQ_PORT"))
rabbit_user = os.getenv("RABBITMQ_USER")
rabbit_pass = os.getenv("RABBITMQ_PASS")

credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
parameters = pika.ConnectionParameters(
    host=rabbit_host,
    port=rabbit_port,
    virtual_host="/",
    credentials=credentials
)

# Conexión y canal global
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='dinners', exchange_type='fanout')



@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/register-transaction")
async def register_transaction(query: RawTransaction):
    data = jsonable_encoder(query)
    channel.basic_publish(
        exchange='dinners',
        routing_key='',
        body=json.dumps(data)
    )
    return {"status": "sent", "transaction": query.dict()}

@app.get("/payments")
def get_payments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, monto_original, monto_final, ntarjeta, codigo, fecha FROM payments ORDER BY fecha DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": r[0], "monto_original": r[1], "monto_final": r[2], "ntarjeta": r[3], "codigo": r[4], "fecha": r[5]}
        for r in rows
    ]

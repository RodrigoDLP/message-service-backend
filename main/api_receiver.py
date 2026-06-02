import pika, sys, os, json
from pydantic import ValidationError

from main.db import get_connection
from main.schemas import RawTransaction, Transaction
from dotenv import load_dotenv

load_dotenv()

def process_transaction(tx: RawTransaction):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                points INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                email VARCHAR(50) NOT NULL,
                monto_original DOUBLE PRECISION NOT NULL,
                monto_final DOUBLE PRECISION NOT NULL,
                codigo VARCHAR(50) NOT NULL,
                ntarjeta BIGINT NOT NULL,
                fecha TIMESTAMP NOT NULL
            )
        """)

        final_amount = tx.amount
        if tx.email:
            cur.execute("SELECT points FROM users WHERE email=%s", (tx.email,))
            row = cur.fetchone()

            if row:
                points = row[0]
                if points >= 80 and tx.amount >= 100:
                    newpoints = points - 80
                    final_amount = tx.amount-100
                else:
                    newpoints = points + 20
                cur.execute("UPDATE users SET points=%s WHERE email=%s", (newpoints, tx.email))
            else:
                newpoints = 20
                cur.execute("INSERT INTO users (email, points) VALUES (%s, %s)", (tx.email, newpoints))

            output = Transaction(
                original_amount=tx.amount,
                final_amount=final_amount,
                creditcard=tx.creditcard,
                codigo=tx.codigo,
                email=tx.email,
                total_points=newpoints,
                datetime=tx.datetime
            )
        else:
            output = Transaction(
                original_amount=tx.amount,
                final_amount=final_amount,
                creditcard=tx.creditcard,
                codigo=tx.codigo,
                email=None,
                total_points=None,
                datetime=tx.datetime
            )
        cur.execute("""
            INSERT INTO payments (email, monto_original, monto_final, codigo, ntarjeta, fecha)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (tx.email, tx.amount, final_amount, tx.codigo, tx.creditcard, tx.datetime))

        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "transaction": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def callback(ch, method, properties, body):
    data = json.loads(body.decode())
    try:
        tx = RawTransaction(**data)
    except ValidationError as e:
        print(f"Error de validación: {str(e)}")
        return
    result = process_transaction(tx)
    if result["status"] == "error":
        print(f"Error procesando transacción: {result['message']}")
    else:
        print(f"Transacción procesada: {result['transaction']}")


def main():
    credentials = pika.PlainCredentials(os.getenv("RABBITMQ_USER"), os.getenv("RABBITMQ_PASS"))
    parameters = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        virtual_host="/",
        credentials=credentials
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.exchange_declare(exchange='dinners', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(exchange='dinners', queue=queue_name)

    print(' [*] Waiting for logs. To exit press CTRL+C')



    channel.basic_consume(
        queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

if __name__ =='__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        raise

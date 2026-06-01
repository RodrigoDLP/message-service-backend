from datetime import datetime
import json
import pytest
from unittest.mock import patch
from main.api_receiver import process_transaction, callback
from main.schemas import RawTransaction



def test_process_transaction_new_user():
    tx = RawTransaction(
        amount=200,
        creditcard=1234567890123456,
        codigo="XYZ789",
        email="newuser@example.com",
        datetime=datetime.now()
    )
    result = process_transaction(tx)
    assert result["status"] == "success"
    assert result["transaction"].original_amount == 200
    # según la lógica, puede ser 200 o 100 dependiendo de puntos
    assert result["transaction"].final_amount in (200, 100)
    assert result["transaction"].email == "newuser@example.com"


def test_process_transaction_no_email():
    tx = RawTransaction(
        amount=50,
        creditcard=9876543210987654,
        codigo="NOEMAIL",
        email=None,
        datetime=datetime.now()
    )
    result = process_transaction(tx)
    assert result["status"] == "success"
    assert result["transaction"].original_amount == 50
    assert result["transaction"].final_amount == 50
    assert result["transaction"].email is None


def test_process_transaction_existing_user(mocker):
    tx = RawTransaction(
        amount=120,
        creditcard=1111222233334444,
        codigo="EXIST123",
        email="existing@example.com",
        datetime=datetime.now()
    )
    # Simula que el usuario ya existe en la BD con 100 puntos
    mock_conn = mocker.patch("main.api_receiver.get_connection")
    mock_cursor = mock_conn.return_value.cursor.return_value
    mock_cursor.fetchone.return_value = (100,)

    result = process_transaction(tx)
    assert result["status"] == "success"
    assert result["transaction"].original_amount == 120
    # con 100 puntos y monto >=100, se descuenta 100
    assert result["transaction"].final_amount == 20
    assert result["transaction"].email == "existing@example.com"


def test_process_transaction_db_error(mocker):
    tx = RawTransaction(
        amount=75,
        creditcard=5555666677778888,
        codigo="DBFAIL",
        email="fail@example.com",
        datetime=datetime.now()
    )
    # Simula que la conexión a la BD falla
    mocker.patch("main.api_receiver.get_connection", side_effect=Exception("DB connection error"))
    result = process_transaction(tx)
    assert result["status"] == "error"
    assert "DB connection error" in result["message"]


def test_process_transaction_missing_codigo():
    tx = RawTransaction(
        amount=30,
        creditcard=9999000011112222,
        codigo="",
        email="nocodigo@example.com",
        datetime=datetime.now()
    )
    result = process_transaction(tx)
    assert result["status"] == "success"
    assert result["transaction"].original_amount == 30
    assert result["transaction"].final_amount == 30
    assert result["transaction"].codigo == ""


def test_callback_success(mocker, capsys):
    body = json.dumps({
        "amount": 100,
        "creditcard": 1234123412341234,
        "codigo": "OK123",
        "email": "ok@example.com",
        "datetime": datetime.now().isoformat()
    }).encode()
    mocker.patch("main.api_receiver.process_transaction", return_value={"status": "success", "transaction": "fake_tx"})
    callback(None, None, None, body)
    captured = capsys.readouterr()
    assert "Transacción procesada" in captured.out


def test_callback_error(mocker, capsys):
    body = json.dumps({
        "amount": 50,
        "creditcard": 5555666677778888,
        "codigo": "FAIL",
        "email": "fail@example.com",
        "datetime": datetime.now().isoformat()
    }).encode()
    mocker.patch("main.api_receiver.process_transaction", return_value={"status": "error", "message": "DB error"})
    callback(None, None, None, body)
    captured = capsys.readouterr()
    assert "Error procesando transacción" in captured.out

def test_callback_db_down(mocker):
    # Simular un body válido
    body = json.dumps({
        "amount": 100,
        "creditcard": 1234567890123456,
        "codigo": "ABC123",
        "email": "fail@example.com",
        "datetime": "2026-06-01T08:14:21.588578"
    }).encode()

    # Mockear process_transaction para devolver error
    mock_proc = mocker.patch("main.api_receiver.process_transaction",
        return_value={"status": "error", "message": "DB down"})

    # Ejecutar callback
    callback(None, None, None, body)

    # Verificar que process_transaction fue llamado
    #api_proc = mocker.patch("main.api_receiver.process_transaction")
    mock_proc.assert_called_once()

def test_callback_missing_amount(capsys):
    body = json.dumps({
        "creditcard": 9876543210987654,
        "codigo": "XYZ789",
        "email": "user@example.com",
        "datetime": "2026-06-01T08:14:21.588578"
    }).encode()

    callback(None, None, None, body)
    captured = capsys.readouterr()
    assert "Error de validación:" in captured.out
    #assert result["status"] == "error"
    #assert "monto" in result["message"].lower()

def test_callback_missing_codigo(capsys):
    body = json.dumps({
        "amount": 100,
        "creditcard": 9876543210987654,
        "email": "user@example.com",
        "datetime": "2026-06-01T08:14:21.588578"
    }).encode()

    callback(None, None, None, body)

    captured = capsys.readouterr()
    assert "Error de validación:" in captured.out
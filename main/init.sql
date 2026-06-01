CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            points INTEGER DEFAULT 0
        );

CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY,
            email VARCHAR(50),
            monto_original DOUBLE PRECISION NOT NULL,
            monto_final DOUBLE PRECISION NOT NULL,
            codigo VARCHAR(50) NOT NULL,
            ntarjeta BIGINT NOT NULL,
            fecha TIMESTAMP NOT NULL
        )
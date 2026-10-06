import sqlite3
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any, Optional

DB_FILE = "horta.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            valor_ph REAL NOT NULL,
            valor_umidade INTEGER NOT NULL,
            status_solo TEXT NOT NULL,
            intervencao TEXT DEFAULT ''
        )
    """)
    conn.commit()

    # Se a tabela estiver vazia, semeia com dados históricos realistas dos últimos 14 dias
    cursor.execute("SELECT COUNT(*) as total FROM leituras")
    count = cursor.fetchone()["total"]
    if count == 0:
        seed_initial_data(conn)
    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()
    now = datetime.now()
    
    # Simula 14 dias de leituras a cada 4 horas
    readings = []
    base_ph = 5.2  # Começou ácido
    
    for day in range(14, 0, -1):
        for hour in [2, 6, 10, 14, 18, 22]:
            dt = now - timedelta(days=day, hours=24-hour)
            dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # Dinâmica de intervenção no dia 9 (Calagem com calcário)
            intervencao = ""
            if day == 9 and hour == 10:
                intervencao = "Calagem com 250g de Calcário Dolomítico"
            elif day == 5 and hour == 14:
                intervencao = "Adubação com Composto Orgânico e Biofertilizante"
            elif day == 2 and hour == 6:
                intervencao = "Irrigação reforçada (período de estiagem)"

            # O pH sobe gradativamente após o dia 9
            if day > 9:
                base_ph = 5.2 + random.uniform(-0.1, 0.15)
            elif day > 5:
                base_ph += 0.08 + random.uniform(-0.05, 0.05)
                base_ph = min(base_ph, 6.4)
            else:
                base_ph = 6.4 + random.uniform(-0.1, 0.12)

            ph = round(base_ph, 2)
            
            # Umidade oscila entre 40% e 75%
            umidade = int(random.randint(45, 75))
            if day in [3, 2] and hour in [14, 18]:
                umidade = random.randint(32, 42) # período seco

            # Diagnóstico baseado nos valores
            if ph < 5.8:
                status_solo = "Ácido (Necessita Calagem)"
            elif ph > 7.2:
                status_solo = "Alcalino"
            elif umidade < 40:
                status_solo = "Seco (Necessita Irrigação)"
            else:
                status_solo = "Ideal"

            readings.append((dt_str, ph, umidade, status_solo, intervencao))

    cursor.executemany("""
        INSERT INTO leituras (timestamp, valor_ph, valor_umidade, status_solo, intervencao)
        VALUES (?, ?, ?, ?, ?)
    """, readings)
    conn.commit()

def insert_leitura(valor_ph: float, valor_umidade: int, status_solo: str, intervencao: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Se o status não for informado ou genérico, calcula automaticamente
    if not status_solo or status_solo.strip().lower() in ["string", "n/a", "auto"]:
        if valor_ph < 5.8:
            status_solo = "Ácido (Necessita Calagem)"
        elif valor_ph > 7.2:
            status_solo = "Alcalino"
        elif valor_umidade < 40:
            status_solo = "Seco (Necessita Irrigação)"
        else:
            status_solo = "Ideal"

    cursor.execute("""
        INSERT INTO leituras (timestamp, valor_ph, valor_umidade, status_solo, intervencao)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, float(valor_ph), int(valor_umidade), status_solo, intervencao or ""))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": new_id,
        "timestamp": timestamp,
        "valor_ph": valor_ph,
        "valor_umidade": valor_umidade,
        "status_solo": status_solo,
        "intervencao": intervencao
    }

def add_intervencao(intervencao_texto: str, data_hora: Optional[str] = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if not data_hora:
        # Pega a leitura mais recente ou insere uma com timestamp atual
        cursor.execute("SELECT id FROM leituras ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE leituras SET intervencao = ? WHERE id = ?", (intervencao_texto, row["id"]))
        else:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO leituras (timestamp, valor_ph, valor_umidade, status_solo, intervencao) VALUES (?, 6.5, 60, 'Ideal', ?)", (ts, intervencao_texto))
    else:
        # Associa à leitura mais próxima da data/hora informada
        cursor.execute("""
            UPDATE leituras 
            SET intervencao = ? 
            WHERE id = (
                SELECT id FROM leituras 
                ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?)) ASC 
                LIMIT 1
            )
        """, (intervencao_texto, data_hora))
    conn.commit()
    conn.close()
    return True

def get_todas_leituras() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras ORDER BY timestamp ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_ultima_leitura() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_intervencoes() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras WHERE intervencao IS NOT NULL AND trim(intervencao) != '' ORDER BY timestamp DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("Banco de dados SQLite inicializado com sucesso!")

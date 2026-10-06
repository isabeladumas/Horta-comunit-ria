import serial
import serial.tools.list_ports
import time
import re
import argparse
import sys
from database import init_db, insert_leitura

def detectar_porta():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    # Prioriza dispositivos comuns de ESP32 / Arduino
    for p in ports:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "usb" in desc or "arduino" in desc:
            return p.device
    # Se não achar por descrição específica, pega a primeira
    return ports[0].device

def monitorar_serial(porta=None, baudrate=115200):
    init_db()

    if not porta:
        porta = detectar_porta()

    if not porta:
        print("[SERIAL] Nenhuma porta COM detectada. Conecte o ESP32 ao USB.")
        return

    print("=" * 65)
    print(f"[CONSUMIDOR SERIAL IOT] ESP32 CONECTADO EM {porta}")
    print(f"Velocidade: {baudrate} baud | Lendo saida de arduino.ino...")
    print("=" * 65)

    re_ph = re.compile(r"pH Simulado:\s*([0-9.]+)", re.IGNORECASE)
    re_umid = re.compile(r"Umidade Simulada:\s*([0-9.]+)", re.IGNORECASE)
    re_status = re.compile(r"Estado do Solo:\s*(.+)", re.IGNORECASE)

    current_ph = None
    current_umid = None
    current_status = None

    while True:
        try:
            ser = serial.Serial(porta, baudrate, timeout=2)
            print(f"[SERIAL] Conexao estabelecida com sucesso na porta {porta}!")

            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # Extrai os dados das linhas geradas pelo arduino.ino
                m_ph = re_ph.search(line)
                if m_ph:
                    current_ph = float(m_ph.group(1))

                m_umid = re_umid.search(line)
                if m_umid:
                    current_umid = float(m_umid.group(1))

                m_status = re_status.search(line)
                if m_status:
                    current_status = m_status.group(1).strip()

                # Quando completar um ciclo (ou encontrar o divisor '---')
                if current_ph is not None and current_umid is not None and current_status is not None:
                    # Grava no banco de dados SQLite
                    reg = insert_leitura(
                        valor_ph=current_ph,
                        valor_umidade=int(round(current_umid)),
                        status_solo=current_status
                    )

                    print(f"[{reg['timestamp']}] [ESP32 COM3] -> pH: {current_ph:.2f} | Umidade: {int(current_umid)}% | Status: '{current_status}' -> Salvo no Banco (ID #{reg['id']})")

                    # Reseta para o próximo ciclo
                    current_ph = None
                    current_umid = None
                    current_status = None

        except serial.SerialException as e:
            print(f"[SERIAL] Porta {porta} desconectada ou ocupada: {e}")
            print("[SERIAL] Tentando reconectar em 3 segundos...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\n[SERIAL] Monitoramento serial encerrado pelo usuario.")
            break
        except Exception as e:
            print(f"[SERIAL] Erro inesperado: {e}")
            time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consumidor Serial ESP32/Arduino")
    parser.add_argument("--port", type=str, default=None, help="Porta COM (ex: COM3)")
    parser.add_argument("--baud", type=int, default=115200, help="Velocidade (padrao: 115200)")
    args = parser.parse_args()

    monitorar_serial(args.port, args.baud)

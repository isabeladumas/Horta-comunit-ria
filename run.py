import sys
import subprocess
import time
import webbrowser
import os
import serial.tools.list_ports

def detectar_porta_serial():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "usb" in desc or "arduino" in desc:
            return p.device
    if ports:
        return ports[0].device
    return None

def main():
    print("=" * 65)
    print("  INICIALIZANDO SISTEMA IOT - HORTA COMUNITARIA")
    print("=" * 65)
    print(f"Interpretador Python: {sys.executable}")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    processos = []

    # 1. Inicia o Servidor de Ingestao API FastAPI (Porta 8000)
    print("\n[1/3] Iniciando Servidor API FastAPI (Porta 8000)...")
    server_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processos.append(("API FastAPI", server_process))
    time.sleep(2)

    if server_process.poll() is not None:
        print("[ERRO] Falha ao iniciar server.py:")
        print(server_process.stdout.read())
        return

    print("      -> Servidor API ativo em: http://localhost:8000")
    print("      -> Documentacao interativa: http://localhost:8000/docs")

    # 2. Conecta ao ESP32 via USB Serial se estiver conectado
    porta_com = detectar_porta_serial()
    if porta_com:
        print(f"\n[2/3] Conectando ao ESP32 via USB ({porta_com})...")
        serial_process = subprocess.Popen(
            [sys.executable, "serial_reader.py", "--port", porta_com],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processos.append(("Consumidor Serial ESP32", serial_process))
        time.sleep(1)
        print(f"      -> Consumindo leituras de {porta_com} (arduino.ino) em tempo real!")
    else:
        print("\n[2/3] Nenhuma porta USB detectada. Aguardando conexoes via Wi-Fi HTTP na porta 8000.")

    # 3. Inicia o Dashboard Streamlit (Porta 8501)
    print("\n[3/3] Iniciando Dashboard Analitico Streamlit (Porta 8501)...")
    dashboard_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "dashboard.py", "--server.port=8501", "--server.headless=true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processos.append(("Dashboard Streamlit", dashboard_process))
    time.sleep(3)

    if dashboard_process.poll() is not None:
        print("[ERRO] Falha ao iniciar dashboard.py:")
        print(dashboard_process.stdout.read())
        for nome, p in processos:
            if p.poll() is None: p.terminate()
        return

    print("      -> Dashboard ativo em: http://localhost:8501")
    print("\n" + "=" * 65)
    print("  SISTEMA COMPLETO EM EXECUCAO!")
    print("  Os dados do ESP32 estao sendo gravados e exibidos ao vivo.")
    print("  Abrindo o navegador em: http://localhost:8501")
    print("  (Para encerrar tudo, pressione CTRL + C neste terminal)")
    print("=" * 65 + "\n")

    try:
        webbrowser.open("http://localhost:8501")
    except Exception:
        pass

    try:
        while True:
            time.sleep(1)
            for nome, p in processos:
                if p.poll() is not None:
                    print(f"\n[AVISO] Processo '{nome}' encerrou.")
                    return
    except KeyboardInterrupt:
        print("\n[ENCERRANDO] Finalizando todos os servicos...")
    finally:
        for nome, p in processos:
            if p.poll() is None:
                p.terminate()
        print("[OK] Sistema finalizado.")

if __name__ == "__main__":
    main()

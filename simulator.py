import time
import random
import requests
import argparse

API_URL = "http://127.0.0.1:8000/api/leituras"

def simular_envio(qtd_leituras=10, intervalo_segundos=3, url_destino=API_URL):
    print("=" * 60)
    print("[SIMULADOR] HARDWARE IOT (ESP32 / ARDUINO)")
    print(f"Destino da requisicao: {url_destino}")
    print(f"Enviando {qtd_leituras} pacotes com intervalo de {intervalo_segundos}s...")
    print("=" * 60)

    base_ph = 6.4
    for i in range(1, qtd_leituras + 1):
        # Gera flutuacoes realistas
        ph = round(base_ph + random.uniform(-0.15, 0.15), 2)
        umidade = int(random.randint(52, 70))
        
        # Diagnostico
        if ph < 5.8:
            status_solo = "Acido (Necessita Calagem)"
        elif ph > 7.2:
            status_solo = "Alcalino"
        elif umidade < 40:
            status_solo = "Seco (Necessita Irrigacao)"
        else:
            status_solo = "Ideal"

        payload = {
            "valor_ph": ph,
            "valor_umidade": umidade,
            "status_solo": status_solo
        }

        try:
            inicio = time.time()
            resp = requests.post(url_destino, json=payload, timeout=5)
            duracao = (time.time() - inicio) * 1000
            
            if resp.status_code in [200, 201]:
                print(f"[{i:02d}/{qtd_leituras:02d}] [SUCESSO] HTTP {resp.status_code} ({duracao:.0f}ms) | pH={ph:.2f} | Umidade={umidade}% | Status='{status_solo}'")
            else:
                print(f"[{i:02d}/{qtd_leituras:02d}] [ALERTA] HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.ConnectionError:
            print(f"[{i:02d}/{qtd_leituras:02d}] [ERRO] Conexao: Servidor nao esta respondendo em {url_destino}.")
            print("   Certifique-se de que 'python server.py' esta em execucao.")
            break
        except Exception as e:
            print(f"[{i:02d}/{qtd_leituras:02d}] [ERRO] {e}")

        if i < qtd_leituras:
            time.sleep(intervalo_segundos)

    print("\n[CONCLUIDO] Simulacao finalizada com sucesso!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador de Envio ESP32")
    parser.add_argument("--qtd", type=int, default=5, help="Quantidade de leituras a simular")
    parser.add_argument("--intervalo", type=int, default=2, help="Intervalo em segundos entre leituras")
    parser.add_argument("--url", type=str, default=API_URL, help="URL do endpoint receptor")
    args = parser.parse_args()

    simular_envio(args.qtd, args.intervalo, args.url)

# Sistema IoT de Monitoramento e Analise de Horta Comunitaria

Sistema completo de engenharia de dados, ingestao de telemetria IoT, persistencia em banco de dados relacional e analise visual interativa a longo prazo para monitoramento de solo (pH e Umidade) e controle de intervencoes agronomicas.

---

## Estrutura de Arquivos do Projeto

```text
ex080/
├── database.py              # Camada de persistencia SQLite com seed historico realista
├── server.py                # Servidor API FastAPI (Endpoints POST/GET, Webhooks e Exportacoes)
├── dashboard.py             # Dashboard analitico em Streamlit com graficos e formularios
├── serial_reader.py         # Consumidor USB Serial que le a saida do arduino.ino em tempo real
├── run.py                   # Inicializador integrado (API + Consumidor Serial + Dashboard)
├── report_generator.py      # Gerador de relatorios tecnicos em PDF e CSV
├── simulator.py             # Simulador de hardware ESP32 para testes sem placa fisica
├── google_apps_script.js    # Codigo alternativo para nuvem gratuita (Google Sheets + Looker Studio)
├── iniciar_sistema.bat      # Script Windows para iniciar o sistema com 1 duplo-clique
├── arduino/
│   └── arduino.ino          # Codigo Arduino/ESP32 pronto para rodar via USB Serial ou Wi-Fi
└── esp32_firmware/
    └── esp32_firmware.ino   # Firmware C++ alternativo com leitura analogica real de pinos
```

---

## Como Executar o Sistema

### Opcao 1: Inicializacao em 1 Clique (Windows)
Basta dar um duplo-clique no arquivo **`iniciar_sistema.bat`**. 
Ele inicia a API FastAPI, conecta automaticamente ao ESP32 via USB Serial na porta COM detectada (ex: COM3) e abre o Dashboard no seu navegador.

### Opcao 2: Via Linha de Comando (PowerShell / Terminal)
```bash
python run.py
```

- **Dashboard Visual**: `http://localhost:8501`
- **Documentacao da API**: `http://localhost:8000/docs`

---

## Conexao com o ESP32 / Arduino

1. Conecte o ESP32 ao computador via cabo USB.
2. Carregue o arquivo [`arduino/arduino.ino`](arduino/arduino.ino) na placa pela Arduino IDE.
3. O script `serial_reader.py` (ou `run.py`) detectara a porta serial automaticamente (ex: `COM3`) e consumira os valores de pH, umidade e estado do solo continuamente para o banco de dados.

---

## Recursos do Dashboard Analitico

1. **Cartoes em Tempo Real**:
   - Ultimo pH com classificacao de acidez e meta otima (6.0 a 6.8).
   - Ultima Umidade com alarme de deficit hidrico (< 40%).
   - Diagnostico automatico do solo e total de intervencoes.
2. **Series Temporais Interativas**:
   - Curva de tendencia do pH com area ideal sombreada em verde e marcadores de intervencao.
   - Curva de umidade com linha de alarme de estiagem (40%).
3. **Cruzamento de Intervencoes (Causa e Efeito)**:
   - Tabela comparativa e metricas de variacao do solo **Antes vs Depois** de cada acao (calagem, adubacao organica, gesso).
4. **Registro Manual de Intervencoes**:
   - Formulario na barra lateral para registrar calagem e adubacao diretamente pelo navegador.
5. **Relatorios Prontos**:
   - Botao para download instantaneo do **Relatorio Tecnico em PDF** com parecer agronomico.
   - Botao para exportacao da base bruta em **CSV**.


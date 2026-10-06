/*
 * ====================================================================
 * MONITORAMENTO DE HORTA IOT - ESP32
 * ====================================================================
 * Este código funciona de DUAS formas integradas:
 * 1. VIA CABO USB (Serial): O script serial_reader.py consome estes
 *    dados diretamente da porta COM e salva no banco de dados.
 * 2. VIA WI-FI (HTTP POST): Caso informe seu Wi-Fi abaixo, o ESP32
 *    também envia os dados via rede para o servidor local (Porta 8000).
 * ====================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>

// --- CONFIGURAÇÃO DO WI-FI (Opcional - deixe em branco se for usar apenas via USB Serial) ---
const char* WIFI_SSID     = ""; // Ex: "Seu_WiFi"
const char* WIFI_PASSWORD = ""; // Ex: "Sua_Senha"

// IP do computador onde roda o servidor (descubra usando 'ipconfig' no terminal)
const char* API_URL = "http://192.168.1.100:8000/api/leituras";

// Variáveis para armazenar as simulações
float simulacaoPh = 7.0;       // Escala de pH (0 a 14)
float simulacaoUmidade = 60.0; // Percentual de umidade (0% a 100%)

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Inicializa o gerador de números aleatórios
  randomSeed(analogRead(0));
  
  Serial.println("--- Sistema Simulado: pH e Umidade Iniciado ---");

  // Se o usuário preencheu o Wi-Fi, tenta conectar
  if (strlen(WIFI_SSID) > 0) {
    Serial.print("Conectando ao Wi-Fi: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }
}

void loop() {
  // 1. SIMULAÇÃO DE pH (Variação suave entre 6.0 e 8.0)
  float variacaoPh = (random(-10, 11) / 100.0); // Oscilação entre -0.10 e +0.10
  simulacaoPh += variacaoPh;
  simulacaoPh = constrain(simulacaoPh, 6.0, 8.0); // Mantém em faixa segura

  // 2. SIMULAÇÃO DE UMIDADE DO SOLO (Variação entre 30% e 85%)
  float variacaoUmidade = (random(-150, 151) / 100.0); // Oscilação entre -1.5% e +1.5%
  simulacaoUmidade += variacaoUmidade;
  simulacaoUmidade = constrain(simulacaoUmidade, 30.0, 85.0);

  // Estimativa dos valores analógicos brutos (RAW de 0 a 4095 do ADC de 12 bits)
  int rawPhSimulado = map(simulacaoPh * 100, 0, 1400, 0, 4095);
  int rawUmidadeSimulado = map(simulacaoUmidade, 0, 100, 3500, 1500); // Sensor capacitivo: valor menor = mais húmido

  // 3. EXIBIÇÃO NO MONITOR SERIAL (Consumido pelo serial_reader.py)
  Serial.print("pH Simulado: ");
  Serial.print(simulacaoPh, 2);
  Serial.print(" | (RAW Estimado: ");
  Serial.print(rawPhSimulado);
  Serial.println(")");

  Serial.print("Umidade Simulada: ");
  Serial.print(simulacaoUmidade, 1);
  Serial.print("% | (RAW Estimado: ");
  Serial.print(rawUmidadeSimulado);
  Serial.println(")");

  // Avaliação simples do nível de umidade
  String statusSolo = "Ideal";
  if (simulacaoUmidade < 40.0) {
    statusSolo = "Seco (Necessita Rega)";
    Serial.println("Estado do Solo: Seco (Necessita Rega)");
  } else if (simulacaoUmidade < 70.0) {
    statusSolo = "Ideal";
    Serial.println("Estado do Solo: Ideal");
  } else {
    statusSolo = "Encharcado";
    Serial.println("Estado do Solo: Encharcado");
  }

  Serial.println("----------------------------------------");

  // 4. ENVIO VIA WI-FI HTTP POST (Se Wi-Fi estiver conectado)
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(API_URL);
    http.addHeader("Content-Type", "application/json");

    String json = "{";
    json += "\"valor_ph\":" + String(simulacaoPh, 2) + ",";
    json += "\"valor_umidade\":" + String((int)simulacaoUmidade) + ",";
    json += "\"status_solo\":\"" + statusSolo + "\"";
    json += "}";

    int httpResponseCode = http.POST(json);
    if (httpResponseCode > 0) {
      Serial.printf("[HTTP] Sucesso: %d\n", httpResponseCode);
    }
    http.end();
  }

  delay(2000); // Atualiza a cada 2 segundos
}
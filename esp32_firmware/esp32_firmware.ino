/*
 * ====================================================================
 * FIRMWARE ESP32 - MONITORAMENTO DE HORTA COMUNITÁRIA IOT
 * ====================================================================
 * Descrição: Leitura de pH e Umidade do solo e envio periódico para
 *             o Servidor de Ingestão via HTTP/HTTPS POST com JSON.
 * ====================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>

// ----------------- CONFIGURAÇÕES DE REDE WIFI -----------------
const char* WIFI_SSID     = "SUA_REDE_WIFI";
const char* WIFI_PASSWORD = "SUA_SENHA_WIFI";

// ----------------- CONFIGURAÇÕES DO SERVIDOR -----------------
// Opção 1: Servidor Local (substitua pelo IP do computador onde roda o server.py)
const char* API_URL = "http://192.168.1.100:8000/api/leituras";

// Opção 2: Nuvem (Google Apps Script Webhook ou Supabase/Cloud)
// const char* API_URL = "https://script.google.com/macros/s/AKfycb.../exec";

// Intervalo de leitura (em milissegundos) -> 60 segundos por padrão
const unsigned long INTERVALO_LEITURA_MS = 60000;
unsigned long ultimaLeituraMs = 0;

// ----------------- DEFINIÇÃO DE PINOS -----------------
const int PINO_SENSOR_PH      = 34; // Entrada Analógica ADC1 (GPIO 34)
const int PINO_SENSOR_UMIDADE = 35; // Entrada Analógica ADC1 (GPIO 35)
const int LED_STATUS          = 2;  // LED embutido para indicação visual

// Função para converter leitura analógica em pH
float lerSensorPH() {
  int valorADC = analogRead(PINO_SENSOR_PH);
  float tensao = valorADC * (3.3 / 4095.0);
  
  // Calibração padrão do sensor de pH (ex: módulo 4502C)
  // Equação típica: pH = 7.0 + ((V_neutro - V_lido) * sensibilidade)
  // Ajuste os valores conforme sua calibração com solução padrão 4.0 e 7.0:
  float valor_ph = 7.0 + ((1.65 - tensao) * 3.5);
  
  // Limites físicos de segurança
  if (valor_ph < 0.0) valor_ph = 0.0;
  if (valor_ph > 14.0) valor_ph = 14.0;
  
  return valor_ph;
}

// Função para converter leitura analógica em Umidade Percentual (%)
int lerSensorUmidade() {
  int valorADC = analogRead(PINO_SENSOR_UMIDADE);
  
  // Sensor Capacitivo ou Resistivo de Umidade:
  // Em geral: Valor seco ~ 3200, Valor na água ~ 1200
  const int ADC_SECO = 3200;
  const int ADC_MOLHADO = 1200;
  
  int umidade = map(valorADC, ADC_SECO, ADC_MOLHADO, 0, 100);
  umidade = constrain(umidade, 0, 100);
  
  return umidade;
}

// Função para classificar o solo conforme regras agronômicas
String obterStatusSolo(float ph, int umidade) {
  if (ph < 5.8) {
    return "Acido (Calagem)";
  } else if (ph > 7.2) {
    return "Alcalino";
  } else if (umidade < 40) {
    return "Seco (Irrigar)";
  } else {
    return "Ideal";
  }
}

// Função de Transmissão HTTP POST com JSON
void enviarDadosNuvem(float ph, int umidade, String status_solo) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Falha: WiFi desconectado. Tentando reconectar...");
    WiFi.reconnect();
    return;
  }

  HTTPClient http;
  http.begin(API_URL);
  
  // IMPORTANTE: Permite seguir redirecionamentos HTTP 302 (obrigatório se usar Google Apps Script)
  http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS);
  http.setTimeout(10000); // 10 segundos de timeout
  http.addHeader("Content-Type", "application/json");

  // Montagem do payload JSON
  // {"valor_ph": 6.5, "valor_umidade": 60, "status_solo": "Ideal"}
  String payload = "{";
  payload += "\"valor_ph\":" + String(ph, 2) + ",";
  payload += "\"valor_umidade\":" + String(umidade) + ",";
  payload += "\"status_solo\":\"" + status_solo + "\"";
  payload += "}";

  Serial.println("[HTTP] Enviando payload: " + payload);
  
  digitalWrite(LED_STATUS, HIGH); // Acende LED durante a transmissão
  int httpCode = http.POST(payload);
  digitalWrite(LED_STATUS, LOW);

  if (httpCode > 0) {
    Serial.printf("[HTTP] Sucesso! Código de resposta: %d\n", httpCode);
    String resposta = http.getString();
    Serial.println("[HTTP] Resposta do Servidor: " + resposta);
  } else {
    Serial.printf("[HTTP] Erro na transmissão: %s (código: %d)\n", http.errorToString(httpCode).c_str(), httpCode);
  }

  http.end();
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);

  // Configuração do ADC para maior estabilidade
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  Serial.println("\n--- INICIALIZANDO MONITORAMENTO DE HORTA IOT ---");
  Serial.print("Conectando ao WiFi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_STATUS, !digitalRead(LED_STATUS));
  }
  
  digitalWrite(LED_STATUS, LOW);
  Serial.println("\n[WIFI] Conectado com sucesso!");
  Serial.print("[WIFI] Endereço IP do ESP32: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  unsigned long agora = millis();
  
  if (agora - ultimaLeituraMs >= INTERVALO_LEITURA_MS || ultimaLeituraMs == 0) {
    ultimaLeituraMs = agora;

    // Realiza as medições
    float ph = lerSensorPH();
    int umidade = lerSensorUmidade();
    String status_solo = obterStatusSolo(ph, umidade);

    Serial.println("\n-------------------------------------------");
    Serial.printf("Leitura realizada:\n");
    Serial.printf(" > pH: %.2f\n", ph);
    Serial.printf(" > Umidade: %d %%\n", umidade);
    Serial.printf(" > Diagnóstico: %s\n", status_solo.c_str());

    // Transmite para a API / Nuvem
    enviarDadosNuvem(ph, umidade, status_solo);
  }

  delay(100);
}

/**
 * ====================================================================
 * SCRIPT RECEPTOR GOOGLE APPS SCRIPT (GOOGLE SHEETS WEBHOOK)
 * ====================================================================
 * Cole este código no editor do Google Apps Script (Extensões > Apps Script)
 * da sua planilha Google Sheets ('Horta_IoT_Database').
 * ====================================================================
 */

const NOME_ABA = "Leituras";

function doPost(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(NOME_ABA);
    let payload;

    // Parse do JSON recebido do ESP32
    if (e.postData && e.postData.contents) {
      payload = JSON.parse(e.postData.contents);
    } else {
      payload = e.parameter;
    }

    const timestamp = Utilities.formatDate(new Date(), "America/Sao_Paulo", "yyyy-MM-dd HH:mm:ss");
    const ph = parseFloat(payload.valor_ph);
    const umidade = parseInt(payload.valor_umidade, 10);
    const status = payload.status_solo || "Ideal";
    const intervencao = payload.intervencao || "";

    // Grava nova linha na planilha
    sheet.appendRow([timestamp, ph, umidade, status, intervencao]);

    return ContentService.createTextOutput(
      JSON.stringify({
        status: "sucesso",
        mensagem: "Linha gravada na planilha",
        data: { timestamp, ph, umidade, status }
      })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "erro", detalhe: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(NOME_ABA);
    const p = e.parameter;

    if (!p.valor_ph || !p.valor_umidade) {
      return ContentService.createTextOutput(
        JSON.stringify({ status: "erro", mensagem: "Parametros ausentes" })
      ).setMimeType(ContentService.MimeType.JSON);
    }

    const timestamp = Utilities.formatDate(new Date(), "America/Sao_Paulo", "yyyy-MM-dd HH:mm:ss");
    const ph = parseFloat(p.valor_ph);
    const umidade = parseInt(p.valor_umidade, 10);
    const status = p.status_solo || "Ideal";
    const intervencao = p.intervencao || "";

    sheet.appendRow([timestamp, ph, umidade, status, intervencao]);

    return ContentService.createTextOutput(
      JSON.stringify({ status: "sucesso", metodo: "GET" })
    ).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(
      JSON.stringify({ status: "erro", detalhe: err.toString() })
    ).setMimeType(ContentService.MimeType.JSON);
  }
}

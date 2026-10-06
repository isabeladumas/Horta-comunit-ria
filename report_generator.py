import os
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from database import get_todas_leituras, get_intervencoes

def generate_csv_buffer() -> io.StringIO:
    leituras = get_todas_leituras()
    df = pd.DataFrame(leituras)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    buffer.seek(0)
    return buffer

def generate_pdf_bytes() -> bytes:
    leituras = get_todas_leituras()
    intervencoes = get_intervencoes()
    df = pd.DataFrame(leituras)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E4620'),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#4A5568'),
        spaceAfter=15
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2E7D32'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#2D3748')
    )

    elements = []

    # Cabeçalho
    elements.append(Paragraph("Relatório Técnico: Monitoramento de Horta Comunitária", title_style))
    elements.append(Paragraph(f"Projeto de Extensão Universitária & Educação Ambiental | Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=15))

    # Resumo Estatístico
    if not df.empty:
        total_leituras = len(df)
        media_ph = df['valor_ph'].mean()
        min_ph = df['valor_ph'].min()
        max_ph = df['valor_ph'].max()
        media_umidade = df['valor_umidade'].mean()
        min_umidade = df['valor_umidade'].min()

        kpi_data = [
            [
                Paragraph("<b>Total de Leituras IoT</b>", body_style),
                Paragraph("<b>pH Médio do Período</b>", body_style),
                Paragraph("<b>Faixa de pH Registrada</b>", body_style),
                Paragraph("<b>Umidade Média do Solo</b>", body_style)
            ],
            [
                Paragraph(f"<font size=14 color='#1B5E20'><b>{total_leituras}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#2E7D32'><b>{media_ph:.2f}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#4A5568'><b>{min_ph:.2f} a {max_ph:.2f}</b></font>", body_style),
                Paragraph(f"<font size=14 color='#0277BD'><b>{media_umidade:.1f}%</b> (mín: {min_umidade}%)</font>", body_style)
            ]
        ]

        t_kpi = Table(kpi_data, colWidths=[120, 130, 130, 140])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4FBF4')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#C8E6C9')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E8F5E9')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(t_kpi)

    # Registro de Intervenções e Análise de Resposta
    elements.append(Paragraph("1. Registro de Intervenções Humanas (Manejo do Solo)", h2_style))
    if intervencoes:
        interv_data = [
            [
                Paragraph("<b>Data/Hora</b>", body_style),
                Paragraph("<b>Intervenção / Ação Registrada</b>", body_style),
                Paragraph("<b>pH no Momento</b>", body_style),
                Paragraph("<b>Umidade</b>", body_style),
                Paragraph("<b>Diagnóstico</b>", body_style)
            ]
        ]
        for it in intervencoes:
            interv_data.append([
                Paragraph(str(it['timestamp']), body_style),
                Paragraph(f"<b>{it['intervencao']}</b>", body_style),
                Paragraph(f"{it['valor_ph']:.2f}", body_style),
                Paragraph(f"{it['valor_umidade']}%", body_style),
                Paragraph(str(it['status_solo']), body_style)
            ])
        t_interv = Table(interv_data, colWidths=[110, 200, 65, 65, 80])
        t_interv.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E8F5E9')),
            ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#81C784')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#C8E6C9')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(t_interv)
    else:
        elements.append(Paragraph("Nenhuma intervenção manual foi registrada até o momento.", body_style))

    # Últimas 15 Leituras Detalhadas
    elements.append(Paragraph("2. Histórico das Últimas Leituras dos Sensores", h2_style))
    if not df.empty:
        ultimas = df.tail(15).iloc[::-1]  # Mais recentes primeiro
        readings_data = [
            [
                Paragraph("<b>Data e Hora</b>", body_style),
                Paragraph("<b>pH Lido</b>", body_style),
                Paragraph("<b>Umidade (%)</b>", body_style),
                Paragraph("<b>Status do Solo</b>", body_style),
                Paragraph("<b>Intervenção</b>", body_style)
            ]
        ]
        for _, row in ultimas.iterrows():
            readings_data.append([
                Paragraph(str(row['timestamp']), body_style),
                Paragraph(f"{row['valor_ph']:.2f}", body_style),
                Paragraph(f"{row['valor_umidade']}%", body_style),
                Paragraph(str(row['status_solo']), body_style),
                Paragraph(str(row['intervencao']) if row['intervencao'] else "-", body_style)
            ])
        t_read = Table(readings_data, colWidths=[115, 65, 75, 120, 145])
        t_read.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(t_read)

    # Conclusões e Recomendações Técnicas
    elements.append(Paragraph("3. Parecer Agronômico & Análise de Longo Prazo", h2_style))
    if not df.empty:
        ultimo_ph = df.iloc[-1]['valor_ph']
        ultimo_umid = df.iloc[-1]['valor_umidade']
        recomendacao = []
        if ultimo_ph < 6.0:
            recomendacao.append("• <b>Acidez do Solo:</b> O pH atual está abaixo da faixa recomendada (6.0 a 6.8). Recomenda-se acompanhamento da calagem ou nova dosagem leve de calcário agrícola.")
        elif ultimo_ph > 7.0:
            recomendacao.append("• <b>Alcalinidade:</b> Solo com tendência alcalina. Evitar fontes calcárias e aplicar matéria orgânica compostada.")
        else:
            recomendacao.append("• <b>pH em Nível Ótimo:</b> Solo equilibrado para absorção de macro e micronutrientes pelas hortaliças.")

        if ultimo_umid < 45:
            recomendacao.append("• <b>Atenção à Irrigação:</b> Umidade abaixo da capacidade ideal de campo. Programar rega nas primeiras horas da manhã.")
        else:
            recomendacao.append("• <b>Nível de Umidade Adequado:</b> Disponibilidade hídrica suficiente para o desenvolvimento radicular.")

        elements.append(Paragraph("<br/>".join(recomendacao), body_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

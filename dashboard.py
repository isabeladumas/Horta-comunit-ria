import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta
import serial.tools.list_ports

from database import (
    init_db,
    get_todas_leituras,
    get_ultima_leitura,
    get_intervencoes,
    insert_leitura,
    add_intervencao
)
from report_generator import generate_pdf_bytes, generate_csv_buffer

# Configuracao da Pagina
st.set_page_config(
    page_title="Horta Comunitaria IoT - Dashboard & Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa banco de dados
init_db()

# Custom CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1b5e20;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .badge-ideal {
        background-color: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
    .badge-alert {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 4px 10px;
        border-radius: 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Detecta status de portas seriais (ESP32)
def obter_status_hardware():
    portas = list(serial.tools.list_ports.comports())
    for p in portas:
        desc = (p.description or "").lower()
        if "cp210" in desc or "ch340" in desc or "usb" in desc or "arduino" in desc:
            return f"[ONLINE] ESP32 Conectado ({p.device})"
    if portas:
        return f"[DETECTADO] Porta ({portas[0].device})"
    return "[AGUARDANDO] ESP32 via Wi-Fi / USB"

# Barra Lateral: Gestao e Acoes Manuais
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1592417817098-8f3d6910985b?w=400&q=80", use_container_width=True)
    st.header("Painel de Operacoes")
    
    st.markdown(f"**Hardware:** `{obter_status_hardware()}`")

    st.subheader("Registrar Intervencao Manual")
    with st.form("form_intervencao", clear_on_submit=True):
        tipo_acao = st.selectbox(
            "Tipo de Acao Agronomica",
            [
                "Calagem (Aplicacao de Calcario Dolomitico)",
                "Aplicacao de Enxofre / Gesso Agricola",
                "Adubacao Organica / Composto / Bokashi",
                "Adubacao Mineral (NPK)",
                "Irrigacao Manual Reforcada",
                "Remocao de Ervas Daninhas / Manejo"
            ]
        )
        detalhes_acao = st.text_input("Detalhes / Quantidade (ex: 200g, 10 Litros)")
        submitted = st.form_submit_button("Salvar Intervencao", use_container_width=True)
        if submitted:
            texto_completo = tipo_acao
            if detalhes_acao:
                texto_completo += f" - {detalhes_acao}"
            add_intervencao(texto_completo)
            st.success("Intervencao registrada com sucesso!")
            st.rerun()

    st.divider()

    st.subheader("Exportacao de Relatorios")
    pdf_data = generate_pdf_bytes()
    st.download_button(
        label="Baixar Relatorio Tecnico (PDF)",
        data=pdf_data,
        file_name=f"relatorio_horta_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    csv_data = generate_csv_buffer().getvalue()
    st.download_button(
        label="Baixar Dados Brutos (CSV)",
        data=csv_data,
        file_name=f"leituras_horta_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.divider()
    st.caption("**Projeto Horta Comunitaria IoT**")
    st.caption("Consumindo dados de: `arduino.ino` (ESP32)")

# Cabecalho Principal
st.markdown('<div class="main-title">Monitoramento Inteligente da Horta Comunitaria</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Telemetria em Tempo Real consumida diretamente do ESP32 (arduino.ino)</div>', unsafe_allow_html=True)

# Funcao com Auto-Refresh a cada 2 segundos via st.fragment
@st.fragment(run_every="2s")
def render_painel_telemetria():
    leituras = get_todas_leituras()
    intervencoes = get_intervencoes()

    if not leituras:
        st.warning("Nenhum dado registrado no momento. Ligue o ESP32 ou inicie o leitor serial.")
        return

    df = pd.DataFrame(leituras)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    ultima = df.iloc[-1]
    penultima = df.iloc[-2] if len(df) > 1 else ultima

    delta_ph = round(float(ultima['valor_ph']) - float(penultima['valor_ph']), 2)
    delta_umid = int(ultima['valor_umidade']) - int(penultima['valor_umidade'])

    # 1. CARDS EM DESTAQUE (Ultimos Valores em Tempo Real)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="pH Atual (ESP32)",
            value=f"{ultima['valor_ph']:.2f}",
            delta=f"{delta_ph:+.2f} vs anterior",
            delta_color="normal"
        )

    with col2:
        st.metric(
            label="Umidade Atual (ESP32)",
            value=f"{ultima['valor_umidade']}%",
            delta=f"{delta_umid:+d}% vs anterior",
            delta_color="normal"
        )

    with col3:
        status = ultima['status_solo']
        badge_style = "badge-ideal" if "Ideal" in status else "badge-alert"
        st.markdown(f"""
            <div style="font-size: 0.85rem; color: #64748b; font-weight: 600; margin-bottom: 8px;">ESTADO DO SOLO</div>
            <div style="margin-top: 4px;"><span class="{badge_style}" style="font-size: 1.05rem;">{status}</span></div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 8px;">Atualizado: {ultima['timestamp'].strftime('%H:%M:%S')}</div>
        """, unsafe_allow_html=True)

    with col4:
        total_interv = len(intervencoes)
        st.metric(
            label="Intervencoes Registradas",
            value=total_interv,
            delta=f"{len(df)} leituras na base",
            delta_color="off"
        )

    st.markdown("---")

    # 2. GRAFICOS DE LINHA TEMPORAIS (pH e UMIDADE)
    tab1, tab2, tab3 = st.tabs(["Curvas de Tendencia (pH e Umidade)", "Analise Cruzada de Intervencoes (Causa e Efeito)", "Tabela de Dados Brutos"])

    with tab1:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("Evolucao Continua do pH")
            st.caption("A faixa verde representa a **Zona Otima Agronomica (6.0 a 6.8)**")

            df_recente = df.tail(50)

            base_ph = alt.Chart(df_recente).encode(
                x=alt.X('timestamp:T', title='Horario', axis=alt.Axis(format='%H:%M:%S')),
                tooltip=[
                    alt.Tooltip('timestamp:T', title='Data/Hora', format='%d/%m/%Y %H:%M:%S'),
                    alt.Tooltip('valor_ph:Q', title='pH Lido', format='.2f'),
                    alt.Tooltip('status_solo:N', title='Status'),
                    alt.Tooltip('intervencao:N', title='Acao Registrada')
                ]
            )

            rect_ideal = alt.Chart(pd.DataFrame({'y1': [6.0], 'y2': [6.8]})).mark_rect(
                opacity=0.15, color='#22c55e'
            ).encode(y='y1:Q', y2='y2:Q')

            line_ph = base_ph.mark_line(color='#16a34a', strokeWidth=2.5, point=alt.OverlayMarkDef(filled=True, fill='#15803d', size=40)).encode(
                y=alt.Y('valor_ph:Q', title='pH', scale=alt.Scale(domain=[5.0, 8.5]))
            )

            df_interv_filter = df_recente[df_recente['intervencao'].str.strip() != '']
            if not df_interv_filter.empty:
                points_interv = alt.Chart(df_interv_filter).mark_point(
                    size=160, color='#dc2626', shape='diamond', filled=True
                ).encode(
                    x='timestamp:T',
                    y='valor_ph:Q',
                    tooltip=[
                        alt.Tooltip('timestamp:T', title='Data da Intervencao', format='%d/%m/%Y %H:%M'),
                        alt.Tooltip('intervencao:N', title='Intervencao'),
                        alt.Tooltip('valor_ph:Q', title='pH')
                    ]
                )
                chart_ph_final = (rect_ideal + line_ph + points_interv).properties(height=350)
            else:
                chart_ph_final = (rect_ideal + line_ph).properties(height=350)

            st.altair_chart(chart_ph_final, use_container_width=True)

        with col_chart2:
            st.subheader("Dinamica de Umidade do Solo")
            st.caption("A linha tracejada vermelha marca o **Limite Critico de Irrigacao (40%)**")

            base_umid = alt.Chart(df_recente).encode(
                x=alt.X('timestamp:T', title='Horario', axis=alt.Axis(format='%H:%M:%S')),
                tooltip=[
                    alt.Tooltip('timestamp:T', title='Data/Hora', format='%d/%m/%Y %H:%M:%S'),
                    alt.Tooltip('valor_umidade:Q', title='Umidade (%)'),
                    alt.Tooltip('status_solo:N', title='Status')
                ]
            )

            rule_seca = alt.Chart(pd.DataFrame({'y': [40]})).mark_rule(
                color='#ef4444', strokeDash=[6, 4], strokeWidth=1.8
            ).encode(y='y:Q')

            area_umid = base_umid.mark_area(
                line={'color': '#0284c7', 'strokeWidth': 2},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#0284c7', offset=0),
                           alt.GradientStop(color='#e0f2fe', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                ),
                opacity=0.6
            ).encode(
                y=alt.Y('valor_umidade:Q', title='Umidade do Solo (%)', scale=alt.Scale(domain=[0, 100]))
            )

            chart_umid_final = (area_umid + rule_seca).properties(height=350)
            st.altair_chart(chart_umid_final, use_container_width=True)

    with tab2:
        st.subheader("Cruzamento de Intervencoes Humanas vs Resposta do Solo")
        st.markdown("""
            Esta analise permite verificar **a eficacia pratica das correcoes aplicadas** (ex: calagem com calcario dolomitico, gesso ou adubacao),
            avaliando como o pH e a umidade responderam nos momentos subsequentes.
        """)

        if not intervencoes:
            st.info("Nenhuma intervencao com anotacao cadastrada. Utilize a barra lateral para registrar.")
        else:
            df_int = pd.DataFrame(intervencoes)
            df_int['timestamp'] = pd.to_datetime(df_int['timestamp'])
            
            st.dataframe(
                df_int[['timestamp', 'intervencao', 'valor_ph', 'valor_umidade', 'status_solo']].rename(columns={
                    'timestamp': 'Data/Hora da Acao',
                    'intervencao': 'Intervencao Realizada',
                    'valor_ph': 'pH no Momento',
                    'valor_umidade': 'Umidade (%)',
                    'status_solo': 'Status'
                }),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Comparativo Antes vs Depois da Intervencao")
            primeira_interv = df_int.sort_values('timestamp').iloc[0]
            data_acao = primeira_interv['timestamp']
            
            df_antes = df[df['timestamp'] < data_acao].tail(5)
            df_depois = df[df['timestamp'] > data_acao].head(10)

            c_antes, c_acao, c_depois = st.columns(3)
            with c_antes:
                media_antes = df_antes['valor_ph'].mean() if not df_antes.empty else float(primeira_interv['valor_ph'])
                st.metric("pH Medio Antes da Acao", f"{media_antes:.2f}", help="Media das leituras anteriores")

            with c_acao:
                st.metric("Intervencao Avaliada", primeira_interv['intervencao'][:35] + "...", f"Em {data_acao.strftime('%d/%m')}")

            with c_depois:
                media_depois = df_depois['valor_ph'].mean() if not df_depois.empty else float(primeira_interv['valor_ph'])
                delta_corr = media_depois - media_antes
                st.metric("pH Medio Pos-Correcao", f"{media_depois:.2f}", delta=f"{delta_corr:+.2f} de variacao", delta_color="normal")

            st.success(f"**Conclusao Agronomica:** A intervencao '{primeira_interv['intervencao']}' elevou o pH de **{media_antes:.2f}** para **{media_depois:.2f}**, aproximando o solo da faixa ideal de cultivo.")

    with tab3:
        st.subheader("Registro Completo de Leituras")
        st.caption("Consulte todas as mensagens recebidas do ESP32.")
        
        st.dataframe(
            df[['id', 'timestamp', 'valor_ph', 'valor_umidade', 'status_solo', 'intervencao']].sort_values('timestamp', ascending=False),
            use_container_width=True,
            hide_index=True
        )

# Renderiza com atualizacao continua
render_painel_telemetria()

"""
nutrition_summary_view.py - Panel visual de conservacion de masa y analitica nutricional.
Integra graficos interactivos Plotly con paleta pastel y verificacion tabular de stock.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def _crear_grafico_conservacion_masa(df_inv: pd.DataFrame) -> go.Figure:
    """Construye un grafico interactivo de barras apiladas (Cocinado vs Reserva) en tonos pasteles."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_inv["nombre"],
        x=df_inv["usado_g"],
        name="Para cocinar (g)",
        orientation="h",
        marker=dict(color="#9AC2A6", line=dict(color="#5E8C6D", width=1)),
        hovertemplate="<b>%{y}</b><br>Cocinado: %{x:.0f} g<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=df_inv["nombre"],
        x=df_inv["restante_g"],
        name="En tu despensa (g)",
        orientation="h",
        marker=dict(color="#EAE4D7", line=dict(color="#CEC5B2", width=1)),
        hovertemplate="<b>%{y}</b><br>Reserva restante: %{x:.0f} g<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack",
        autosize=True,
        height=max(240, len(df_inv) * 38 + 70),
        margin=dict(l=10, r=15, t=28, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", size=12, color="#303E32"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, entrywidth=1, entrywidthmode="fraction"),
        xaxis=dict(title="Cantidad (g)", gridcolor="#E9E4DC", zeroline=False, automargin=True),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)"),
        transition=dict(duration=0),
    )
    return fig


def _crear_grafico_macros_plan(platos: list[dict]) -> go.Figure:
    """Construye un grafico pastel de aporte total de macronutrientes en gramos del plan activo."""
    tot_p = sum(p["macros_por_porcion"]["proteina_g"] * p["porciones"] for p in platos if p["porciones"] > 0)
    tot_c = sum(p["macros_por_porcion"]["carbohidratos_g"] * p["porciones"] for p in platos if p["porciones"] > 0)
    tot_g = sum(p["macros_por_porcion"]["grasa_g"] * p["porciones"] for p in platos if p["porciones"] > 0)
    tot_f = sum((p["macros_por_porcion"].get("fibra_g") or 0.0) * p["porciones"] for p in platos if p["porciones"] > 0)

    categorias = ["Proteína", "Carbohidratos", "Grasas", "Fibra"]
    valores = [round(tot_p, 1), round(tot_c, 1), round(tot_g, 1), round(tot_f, 1)]
    colores = ["#C3C6EB", "#F0DFAD", "#B8D7EB", "#B5D8BE"]
    bordes = ["#7C81B8", "#B89F56", "#6D9BB8", "#5E8C6D"]

    fig = go.Figure(go.Bar(
        x=categorias,
        y=valores,
        text=[f"{v:.1f} g" for v in valores],
        textposition="outside",
        marker=dict(color=colores, line=dict(color=bordes, width=1.2)),
        hovertemplate="<b>%{x}</b><br>Total del lote: %{y:.1f} g<extra></extra>",
    ))
    fig.update_layout(
        height=275,
        autosize=True,
        margin=dict(l=10, r=10, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", size=12, color="#303E32"),
        yaxis=dict(title="Gramos acumulados (g)", gridcolor="#E9E4DC", zeroline=False),
        xaxis=dict(gridcolor="rgba(0,0,0,0)", automargin=True),
        transition=dict(duration=0),
    )
    return fig


def render_nutrition_summary_view(plan: dict, modo_actual: str) -> None:
    """Renderiza el balance cuantitativo de masa, graficos interactivos y tabla de auditoria."""
    if not plan or not plan.get("metricas"):
        return

    st.markdown('<h3 class="editorial-title">Cada ingrediente cuenta</h3>', unsafe_allow_html=True)
    st.markdown("""
    <div class="guide-panel">
        <b>Un plan que cuida tu despensa.</b> Aquí puedes ver cuánto usarás en tus recetas y qué quedará para otra comida.
        Las cantidades del plan siempre respetan lo que tienes disponible.
    </div>
    """, unsafe_allow_html=True)

    met = plan["metricas"]
    with st.container(key="plan-metrics"):
        columnas = st.columns(4)
        for col, titulo, valor in zip(columnas, ["Aprovechamiento", "Para cocinar", "Frescos utilizados", "Porciones"],
                                      [f'{met["porcentaje_uso"]}%', f'{met["kg_utilizado"]} kg',
                                       f'{met["kg_prioridad_alta_usado"]} kg', str(met["porciones_totales"])]):
            col.markdown(f'<div class="metric-tile"><div class="metric-label">{titulo}</div><div class="metric-value">{valor}</div></div>', unsafe_allow_html=True)

    df_inv = pd.DataFrame(plan["inventario"])
    if not df_inv.empty:
        tabs_graf = st.tabs(["Ingredientes", "Nutrientes"], key="grafico_plan", on_change="rerun")
        if tabs_graf[0].open:
            with tabs_graf[0]:
                fig_masa = _crear_grafico_conservacion_masa(df_inv)
                st.plotly_chart(fig_masa, width="stretch", config={"displayModeBar": False, "responsive": True},
                                alt="Gramos utilizados y disponibles de cada ingrediente")
        if tabs_graf[1].open:
            with tabs_graf[1]:
                fig_mac = _crear_grafico_macros_plan(plan.get("platos", []))
                st.plotly_chart(fig_mac, width="stretch", config={"displayModeBar": False, "responsive": True},
                                alt="Proteína, carbohidratos, grasas y fibra del plan en gramos")

        st.markdown("#### Tu despensa después de cocinar")
        df_mostrar = df_inv[["nombre", "prioridad", "inicial_g", "usado_g", "restante_g"]].copy()
        df_mostrar["uso_pct"] = (df_mostrar["usado_g"] / df_mostrar["inicial_g"].replace(0, 1) * 100.0).round(1)
        st.dataframe(
            df_mostrar,
            column_config={
                "nombre": st.column_config.TextColumn("Alimento"),
                "prioridad": st.column_config.TextColumn("Prioridad"),
                "inicial_g": st.column_config.NumberColumn("Disponible", format="%.0f g"),
                "usado_g": st.column_config.NumberColumn("Para cocinar", format="%.0f g"),
                "restante_g": st.column_config.NumberColumn("Quedará", format="%.0f g"),
                "uso_pct": st.column_config.ProgressColumn("Uso (%)", min_value=0, max_value=100, format="%.1f%%"),
            },
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("""
    <div class="op-card pastel-butter" style="margin-top:0.9rem; font-size:0.8rem; line-height:1.5;">
        <b>Antes de ponerte el delantal:</b> Los nutrientes se calculan con referencias por 100 g de USDA / INCAP.
        Revisa siempre la frescura, los alérgenos y la cocción de tus alimentos.
    </div>
    """, unsafe_allow_html=True)

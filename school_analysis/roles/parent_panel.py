import streamlit as st
import plotly.express as px
import pandas as pd

from school_analysis.analytics import overview as ov
from school_analysis.analytics import reports


def show(df: pd.DataFrame, student_id: int, student_name: str):
    st.header(f"👨‍👩‍👧 Отчёт по ученику: {student_name}")

    tab1, tab2, tab3 = st.tabs(["Успеваемость по месяцам", "Сравнение с классом", "PDF отчёт"])

    with tab1:
        summary = ov.parent_monthly_summary(df, student_id)
        st.dataframe(summary, use_container_width=True)
        if not summary.empty:
            fig = px.line(summary, x='month_id', y='avg_percent', color='subject', markers=True)
            fig.update_layout(yaxis=dict(range=[0, 100]))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Пока нет данных по месяцам.")

    with tab2:
        comparison_df = ov.parent_comparison_with_class(df, student_id)
        st.dataframe(comparison_df, use_container_width=True)
        if not comparison_df.empty:
            colors = ['#4CAF50' if x > 0 else '#F44336' for x in comparison_df['difference']]
            fig = px.bar(comparison_df, x='subject', y='difference', color=colors)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Недостаточно данных для сравнения с классом.")

    with tab3:
        st.subheader("📄 Сформировать PDF-отчёт")
        summary = ov.parent_monthly_summary(df, student_id)
        comparison_df = ov.parent_comparison_with_class(df, student_id)

        if st.button("💾 Сформировать PDF"):
            pdf_buf = reports.generate_pdf_report(student_name, summary, comparison_df)
            st.download_button(
                "📥 Скачать PDF",
                pdf_buf,
                file_name=f"report_{student_name}.pdf",
                mime="application/pdf"
            )

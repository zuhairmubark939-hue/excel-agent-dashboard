import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Agent Excel Dashboard", layout="wide")

st.title("🤖 AI Agent Excel Dashboard (Gemini)")
st.write("قم برفع ملف الإكسل ليقوم الـ Agent بتحليله وتوليد الداشبورد تلقائياً:")

api_key = st.sidebar.text_input("أدخل مفتاح Google Gemini API Key:", type="password")
uploaded_file = st.file_uploader("اختر ملف الإكسل (.xlsx)", type=["xlsx", "xls"])


@st.cache_data(show_spinner=False)
def load_data(file):
    return pd.read_excel(file)


@st.cache_data(show_spinner=False)
def get_agent_config(api_key: str, summary_json: str) -> dict:
    client = genai.Client(api_key=api_key)
    prompt = f"""
    بناءً على أعمدة وبيانات الملف التالية:
    {summary_json}

    اختر أفضل عمود رقمي (kpi_column) وأفضل عمود فئوي (group_column) للتوزيع.
    أرجع JSON فقط بالهيكل التالي:
    {{
      "kpi_column": "اسم العمود الرقمي لحساب الإجمالي",
      "group_column": "اسم العمود الفئوي للتوزيع",
      "chart_title": "عنوان الرسم البياني"
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)


if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.success("تم تحميل الملف بنجاح!")

    if api_key:
        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        summary = {
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "sample_data": df.head(5).to_dict(orient="records"),
        }

        try:
            with st.spinner("جاري تحليل البيانات بواسطة الـ Agent..."):
                agent_config = get_agent_config(
                    api_key, json.dumps(summary, default=str, ensure_ascii=False)
                )

            kpi_col = agent_config.get("kpi_column")
            group_col = agent_config.get("group_column")
            title = agent_config.get("chart_title", "تحليل البيانات")

            col1, col2 = st.columns(2)
            if kpi_col in numeric_cols:
                col1.metric(f"إجمالي {kpi_col}", f"{df[kpi_col].sum():,.2f}")
                col2.metric(f"متوسط {kpi_col}", f"{df[kpi_col].mean():,.2f}")

            st.markdown("---")

            if kpi_col in numeric_cols and group_col in df.columns:
                grouped = df.groupby(group_col, as_index=False)[kpi_col].sum()
                fig = px.bar(grouped, x=group_col, y=kpi_col,
                             title=title, color=group_col)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("تعذر اختيار أعمدة مناسبة، عرض تلقائي للبيانات:")
                st.dataframe(df)

        except Exception as e:
            st.error(f"حدث خطأ أثناء معالجة الـ Agent: {e}")
    else:
        st.warning("يرجى إدخال مفتاح Gemini API Key في الشريط الجانبي.")

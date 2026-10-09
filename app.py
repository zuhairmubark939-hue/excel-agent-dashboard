import streamlit as st
import pandas as pd
import plotly.express as px
import json
from google import genai

st.set_page_config(page_title="AI Agent Excel Dashboard", layout="wide")

st.title("🤖 AI Agent Excel Dashboard (Gemini)")
st.write("قم برفع ملف الإكسل ليقوم الـ Agent بتحليله وتوليد الداشبورد تلقائياً:")

api_key = st.sidebar.text_input("أدخل مفتاح Google Gemini API Key:", type="password")

uploaded_file = st.file_uploader("اختر ملف الإكسل (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("تم تحميل الملف بنجاح!")
    
    if api_key:
        client = genai.Client(api_key=api_key)
        
        summary = {
            "columns": list(df.columns),
            "sample_data": df.head(5).to_dict(orient="records")
        }
        
        with st.spinner("جاري تحليل البيانات بواسطة الـ Agent وتوليد المخططات..."):
            prompt = f"""
            بناءً على أعمدة وبيانات الملف التالية:
            {json.dumps(summary, default=str)}
            
            اختر أفضل المخططات المناسبة. قم بإرجاع JSON فقط بالهيكل التالي بدون أي نص إضافي أو علامات markdown:
            {{
              "kpi_column": "اسم العمود الرقمي لحساب الإجمالي",
              "group_column": "اسم العمود الفئوي/الجمعي للتوزيع",
              "chart_title": "عنوان الرسم البياني"
            }}
            """
            
            try:
                response = client.models.generate_content(
                   model = genai.GenerativeModel('gemini-2.0-flash')
                    contents=prompt,
                )
                
                # تنظيف النص وإزالة أوسمة التنسيق إن وجدت
                clean_text = response.text.replace("```json", "").replace("```", "").strip()
                agent_config = json.loads(clean_text)
                
                kpi_col = agent_config.get("kpi_column")
                group_col = agent_config.get("group_column")
                title = agent_config.get("chart_title", "تحليل البيانات")
                
                col1, col2 = st.columns(2)
                if kpi_col in df.columns:
                    col1.metric(f"إجمالي {kpi_col}", f"{df[kpi_col].sum():,.2f}")
                    col2.metric(f"متوسط {kpi_col}", f"{df[kpi_col].mean():,.2f}")
                
                st.markdown("---")
                
                if group_col in df.columns and kpi_col in df.columns:
                    fig = px.bar(df, x=group_col, y=kpi_col, title=title, color=group_col)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.write("عرض تلقائي للبيانات:")
                    st.dataframe(df)
                    
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الـ Agent: {e}")
    else:
        st.warning("يرجى إدخال مفتاح Gemini API Key في الشريط الجانبي.")

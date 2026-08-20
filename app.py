import streamlit as st
from pypdf import PdfReader

st.set_page_config(page_title="دستیار هوشمند اسناد", page_icon="🤖")
st.title("🤖 دستیار هوشمند اسناد شما")

# بخش سایدبار برای آپلود فایل
with st.sidebar:
    st.header("۱. آپلود مستندات")
    uploaded_file = st.file_uploader("فایل PDF خود را اینجا آپلود کنید", type="pdf")

# بخش اصلی برنامه
if uploaded_file is not None:
    st.success("فایل با موفقیت آپلود شد! ✅")
    
    # استخراج متن از PDF
    pdf_reader = PdfReader(uploaded_file)
    extracted_text = ""
    for page in pdf_reader.pages:
        extracted_text += page.extract_text()
        
    # نمایش یک بخش کوچک از متن برای اطمینان از کارکرد درست
    with st.expander("مشاهده پیش‌نمایش متن استخراج شده"):
        st.write(extracted_text[:1000] + " ... [ادامه دارد]")

    # باکس چت برای گرفتن سوال کاربر
    st.divider()
    st.subheader("۲. پرسش و پاسخ")
    user_question = st.text_input("چه سوالی درباره این سند دارید؟")
    
    if user_question:
        # فعلا یک جواب تستی می‌دهیم تا در فاز بعد هوش مصنوعی را وصل کنیم
        st.info(f"سوال شما دریافت شد: «{user_question}»")
        st.warning("در فاز بعدی، هوش مصنوعی جواب این سوال را از روی متن پیدا خواهد کرد!")

else:
    st.info("لطفاً ابتدا یک فایل PDF از منوی سمت چپ آپلود کنید.")

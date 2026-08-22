import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="Smart Document Assistant", page_icon="🤖")
st.title("🤖 Your Smart Document Assistant")

# Important engineering concept: Using Session State
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

# ==========================================
# UI STEP 1: SIDEBAR REVAMP (BYOK & INFO)
# ==========================================
with st.sidebar:
    st.header("🔑 1. API Settings")
    
    # 1. API Key Mode Selection (Bring Your Own Key)
    api_mode = st.radio(
        "Choose API Key Mode:",
        ["🟢 Use App's Default Key (Free)", "🔑 Use My Own API Key"]
    )
    
    google_api_key = None
    if api_mode == "🟢 Use App's Default Key (Free)":
        # Safely read from secrets.toml (or Streamlit Cloud Secrets)
        if "GOOGLE_API_KEY" in st.secrets:
            google_api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            st.error("⚠️ Server API key not configured. Please use your own key.")
    else:
        # Show password input only if user chooses to bring their own key
        google_api_key = st.text_input("Enter your Google API Key (Gemini):", type="password")
        
    # Educational Tooltip for users/recruiters
    with st.expander("💡 Why use my own key?"):
        st.caption(
            "The public key provided by this site has a daily rate limit from Google. "
            "If the site is experiencing high traffic, you might encounter quota errors. "
            "By providing your own key, you ensure a stable, faster, and completely private connection. "
            "**(Your key is NEVER stored on our servers).**"
        )
    
    st.divider()

    st.header("📄 2. Upload Document")
    uploaded_file = st.file_uploader("Upload your PDF file here", type="pdf")
    

# ==========================================
# MAIN APP FLOW (Unchanged for now)
# ==========================================
if uploaded_file is not None:
    if st.session_state.vector_store is None:
        with st.spinner("Processing and building database... (This may take a few minutes)"):
            
            # 1. Text Extraction
            pdf_reader = PdfReader(uploaded_file)
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text()
            
            # 2. Text Chunking
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200 
            )
            text_chunks = text_splitter.split_text(extracted_text)
            
            # 3. Convert to vectors using a lightweight AI model (no GPU required)
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # 4. Store in Chroma vector database
            vector_store = Chroma.from_texts(
                texts=text_chunks, 
                embedding=embeddings
            )
            
            # Save database in session state
            st.session_state.vector_store = vector_store
            
        st.success("File successfully processed and stored in database! ✅")
        
        with st.expander("View Processing Details"):
            st.write(f"Total pages: {len(pdf_reader.pages)}")
            st.write(f"Your text was split into {len(text_chunks)} small chunks.")

    # Q&A Section
    st.divider()
    st.subheader("💬 3. Smart Q&A")
    user_question = st.text_input("What is your question about this document?")
    
    if user_question:
        if not google_api_key:
            st.error("⚠️ Please enter your Google API Key in the sidebar first.")
        else:
            with st.spinner("Analyzing document and generating answer..."):
                relevant_chunks = st.session_state.vector_store.similarity_search(user_question, k=3)
                context = "\n\n---\n\n".join([chunk.page_content for chunk in relevant_chunks])
                
                llm = ChatGoogleGenerativeAI(
                    model="gemini-flash-latest",
                    google_api_key=google_api_key,
                    temperature=0.3
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", """You are a smart, professional, and accurate assistant. Your task is to answer questions based ONLY on the provided context.
                    
                    Important Rules:
                    1. Answer based ONLY on the text provided below.
                    2. If the answer is not in the text, politely say "I'm sorry, but the answer to this question is not available in the document." Do NOT make up information.
                    3. Provide a clear and complete answer.
                    
                    Context extracted from document:
                    {context}"""),
                    ("human", "User question: {question}")
                ])
                
                chain = prompt | llm | StrOutputParser()
                response = chain.invoke({"context": context, "question": user_question})

                st.success("🤖 AI Answer:")
                st.write(response)
                
                with st.expander("🔍 View the source text used for this answer"):
                    st.write(context)

else:
    st.info("Please upload a PDF file from the left sidebar first.")
# ==========================================
# RENDER SIDEBAR INFO PANEL AT THE END
# ==========================================
# (This ensures the status turns green immediately after processing)
with st.sidebar:
    st.divider()
    st.header("ℹ️ Info Panel")
    st.markdown("**Model:** Gemini Flash Latest")
    
    if st.session_state.vector_store is not None:
        st.markdown("**Database:** 🟢 Ready")
    else:
        st.markdown("**Database:** 🔴 Empty")
    
    st.markdown("[🔗 View Source Code on GitHub](#)")
import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import uuid

st.set_page_config(page_title="Smart Document Assistant", page_icon="🤖")
st.title("🤖 Your Smart Document Assistant")

# --- Hero Section ---
st.markdown("""
Welcome to your intelligent document assistant! 
Upload any lengthy PDF, and I will read it, understand its context, and answer your questions based **strictly** on the document's content.
""")
st.divider()

# Important engineering concept: Using Session State
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False
# NEW: Store chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# UI STEP 1: SIDEBAR (API SETTINGS)
# ==========================================
with st.sidebar:
    st.header("🔑 API Settings")
    api_mode = st.radio(
        "Choose API Key Mode:",
        ["🟢 Use App's Default Key (Free)", "🔑 Use My Own API Key"]
    )
    
    google_api_key = None
    if api_mode == "🟢 Use App's Default Key (Free)":
        if "GOOGLE_API_KEY" in st.secrets:
            google_api_key = st.secrets["GOOGLE_API_KEY"]
        else:
            st.error("⚠️ Server API key not configured. Please use your own key.")
    else:
        google_api_key = st.text_input("Enter your Google API Key (Gemini):", type="password")
        
    with st.expander("💡 Why use my own key?"):
        st.caption(
            "The public key provided by this site has a daily rate limit from Google. "
            "If the site is experiencing high traffic, you might encounter quota errors. "
            "By providing your own key, you ensure a stable, faster, and completely private connection. "
            "**(Your key is NEVER stored on our servers).**"
        )

# ==========================================
# UI STEP 2: DATA INGESTION (MAIN PAGE)
# ==========================================
# 1. If database is EMPTY, show the upload section (Step 1)
if st.session_state.vector_store is None:
    st.header("📥 Step 1: Provide a Document")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

    with col2:
        st.info("💡 Don't have a PDF ready? Try this 👇")
        if st.button("📄 Load Sample Document (Attention Is All You Need)"):
            st.session_state.use_sample = True

    # Logic to determine which file to process
    file_to_process = None
    if uploaded_file is not None:
        file_to_process = uploaded_file
        st.session_state.use_sample = False
    elif st.session_state.use_sample:
        file_to_process = "sample.pdf"

    # Process the file if provided
    if file_to_process is not None:
        with st.spinner("Processing and building database... (This may take a few minutes)"):
            try:
                pdf_reader = PdfReader(file_to_process)
                extracted_text = ""
                for page in pdf_reader.pages:
                    extracted_text += page.extract_text()
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                text_chunks = text_splitter.split_text(extracted_text)
                
                embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})
                vector_store = Chroma.from_texts(
                    texts=text_chunks, 
                    embedding=embeddings,
                    collection_name=f"pdf_rag_{uuid.uuid4().hex}"
                )
                
                # Save to memory and IMMEDIATELY refresh the page to hide Step 1
                st.session_state.vector_store = vector_store
                st.rerun()
                
            except FileNotFoundError:
                st.error("⚠️ Sample file not found! Please make sure 'sample.pdf' exists in the project folder.")
                st.session_state.use_sample = False

# 2. If database is READY, hide Step 1 and show a small Reset button
else:
    st.success("✅ Document processed and database is ready!")
    if st.button("🔄 Upload a different document (Back to Step 1)"):
        st.session_state.vector_store = None
        st.session_state.use_sample = False
        st.session_state.messages = [] # IMPORTANT: Clear chat history when new file is uploaded
        st.rerun() # Refresh to show Step 1 again

# ==========================================
# UI STEP 3: SMART Q&A (CHAT INTERFACE)
# ==========================================
if st.session_state.vector_store is not None:
    st.divider()
    st.subheader("💬 Step 2: Chat with your Document")
    
    # 1. Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display sources if they exist in the message history
            if "source" in message:
                with st.expander("🔍 View the source text used for this answer"):
                    st.write(message["source"])

    # 2. React to user input
    if user_question := st.chat_input("What is your question about this document?"):
        
        if not google_api_key:
            st.error("⚠️ Please enter your Google API Key in the sidebar first.")
        else:
            # Display user message in chat message container
            st.chat_message("user").markdown(user_question)
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_question})
            
            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                with st.spinner("Analyzing document and generating answer..."):
                    relevant_chunks = st.session_state.vector_store.similarity_search(user_question, k=6)
                    context = "\n\n---\n\n".join([chunk.page_content for chunk in relevant_chunks])
                    
                    llm = ChatGoogleGenerativeAI(
                        model="gemini-flash-latest",
                        google_api_key=google_api_key,
                        temperature=0.3
                    )
                    
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", """You are a smart, professional, and accurate assistant. Your task is to answer questions based ONLY on the provided context.
                        
                        Important Rules:
                        1. Answer based ONLY on the text provided below.
                        2. If the answer is not in the text, politely say "I'm sorry, but the answer to this question is not available in the document." Do NOT make up information.
                        3. Provide a clear and complete answer.
                        
                        Context extracted from document:
                        {context}"""),
                        ("human", "User question: {question}")
                    ])
                    
                    chain = prompt_template | llm | StrOutputParser()
                    response = chain.invoke({"context": context, "question": user_question})

                    st.markdown(response)
                    with st.expander("🔍 View the source text used for this answer"):
                        st.write(context)
                
            # Add assistant response and its source to chat history
            st.session_state.messages.append({"role": "assistant", "content": response, "source": context})


# ==========================================
# RENDER SIDEBAR INFO PANEL AT THE END
# ==========================================
with st.sidebar:
    st.divider()
    st.header("ℹ️ Info Panel")
    st.markdown("**Model:** Gemini Flash Latest")
    
    if st.session_state.vector_store is not None:
        st.markdown("**Database:** 🟢 Ready")
    else:
        st.markdown("**Database:** 🔴 Empty")
    
    st.markdown("[🔗 View Source Code on GitHub](#)")
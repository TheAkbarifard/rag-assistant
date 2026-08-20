import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

st.set_page_config(page_title="Smart Document Assistant", page_icon="🤖")
st.title("🤖 Your Smart Document Assistant")

# Important engineering concept: Using Session State
# To prevent processing the file from scratch on every UI interaction,
# we keep the database in the browser's temporary memory.
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Upload your PDF file here", type="pdf")

if uploaded_file is not None:
    # Only process if the database hasn't been created yet
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
    else:
        st.success("Database is ready! ✅")

    # Q&A Section
    st.divider()
    st.subheader("2. Smart Search")
    user_question = st.text_input("What is your question about this document?")
    
    if user_question:
        with st.spinner("Searching the vector database..."):
            # Find top 3 text chunks with highest semantic similarity to the question
            relevant_chunks = st.session_state.vector_store.similarity_search(user_question, k=3)
            
            st.info("🔍 Found these 3 relevant chunks in your document:")
            for i, chunk in enumerate(relevant_chunks):
                with st.expander(f"Reference {i+1}"):
                    st.write(chunk.page_content)
            
            st.warning("In the next phase (final phase), we will feed these found texts to a Language Model (LLM) to generate a human-like answer!")

else:
    st.info("Please upload a PDF file from the left sidebar first.")

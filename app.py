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
# To prevent processing the file from scratch on every UI interaction,
# we keep the database in the browser's temporary memory.
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

with st.sidebar:
    st.header("🔑 1. AI Settings")
    # Securely take the API key from the user
    google_api_key = st.text_input("Enter your Google API Key (Gemini):", type="password")
    
    st.divider()

    st.header("📄 2. Upload Document")
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
    st.subheader("💬 3. Smart Q&A")
    user_question = st.text_input("What is your question about this document?")
    
    if user_question:
        if not google_api_key:
            st.error("⚠️ Please enter your Google API Key in the sidebar first.")
        else:
            with st.spinner("Analyzing document and generating answer..."):
                # 1. Retrieval (R in RAG): Find top 3 relevant chunks
                relevant_chunks = st.session_state.vector_store.similarity_search(user_question, k=3)
                
                # Combine the chunks into a single context string
                context = "\n\n---\n\n".join([chunk.page_content for chunk in relevant_chunks])
                
                # 2. Generation (G in RAG): Initialize Gemini
                llm = ChatGoogleGenerativeAI(
                    model="gemini-flash-latest",
                    google_api_key=google_api_key,
                    temperature=0.3
                )
                
                # Create the prompt template
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
                
                # Create the LangChain LCEL pipeline with a parser
                chain = prompt | llm | StrOutputParser()

                # Execute the chain
                response = chain.invoke({"context": context, "question": user_question})

                # Display the final AI answer (now we can just write 'response' directly)
                st.success("🤖 AI Answer:")
                st.write(response)
                
                # Keep transparency by showing the sources below the answer
                with st.expander("🔍 View the source text used for this answer"):
                    st.write(context)

else:
    st.info("Please upload a PDF file from the left sidebar first.")

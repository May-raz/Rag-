import streamlit as st
from rag import ask

st.title("Medical Assistant")

question = st.chat_input("What do you need to know from the 2 medical books: ")

if question:
    with st.spinner("Searching the books..."):
        result = ask(question)

    labels = []

    for source in result["sources"]:    
        labels.append(f'{source["book"]}, p.{source["page"]}')
    
    st.write(result["answer"])
    # if labels:
    #     st.write("Sources: " + " | ".join(labels))
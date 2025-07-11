import markdown
import os
import pdfkit
from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langsmith import traceable

from src.cv_evaluator import evaluate_cv_quality
from src.prompts.prompts import generate_cv_prompt

# Load env & API key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Brakuje zmiennej środowiskowej OPENAI_API_KEY w .env")

# Init embeddings, vectorstore, chat
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
index_name = os.environ["INDEX_NAME"]
vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
chat = ChatOpenAI(temperature=0.7, verbose=True)


@traceable(name="Generate CV")
def generate_cv(job_description: str, user_id: str = "user_1", additional_comments: str = ""):
    # Build retrieval → generation chain
    retriever = vectorstore.as_retriever(search_kwargs={"filter": {"user_id": user_id}, "k": 5})
    prompt_template = generate_cv_prompt

    stuff_chain = create_stuff_documents_chain(chat, prompt_template)
    qa_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=stuff_chain
    )
    result = qa_chain.invoke({
        "input": job_description,
        "additional_comments": additional_comments
    })
    return result["answer"]


def create_pdf_from_text(text: str, md_path: str = "cv.md", pdf_path: str = "data/cv.pdf",
                         wkhtmltopdf_path: str = None) -> str:
    # 1) Konwersja na Markdown
    md_lines = []
    lines = text.splitlines()
    header_phase = True

    for line in lines:
        stripped = line.strip()
        if not stripped:
            md_lines.append("")
            continue

        if header_phase:
            if ":" in stripped and not stripped.startswith("-"):
                key, val = stripped.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key.lower().startswith("imię nazwisko"):
                    md_lines.append(f"# {val}")
                else:
                    md_lines.append(f"**{key}:** {val}")
                continue
            else:
                header_phase = False

        if stripped.endswith(":"):
            heading = stripped[:-1].strip()
            md_lines.append(f"## {heading}")
            continue

        if stripped.startswith("-"):
            md_lines.append(stripped)
            continue

        md_lines.append(stripped)

    md_text = "\n".join(md_lines)

    # Zapisz Markdown do pliku (opcjonalne)
    # with open(md_path, "w", encoding="utf-8") as f:
    #     f.write(md_text)

    # Konwersja Markdown → HTML
    html_body = markdown.markdown(md_text, extensions=["extra", "smarty"])
    html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>CV</title>
      </head>
      <body>
        {html_body}
      </body>
    </html>
    """
    # Generowanie PDF z HTML
    # Jeśli wkhtmltopdf nie jest w PATH, podaj ścieżkę:
    config = None
    if wkhtmltopdf_path:
        config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    options = {"encoding": "UTF-8"}
    pdfkit.from_string(html, pdf_path, configuration=config, options=options)

    return os.path.abspath(pdf_path)


# PRZYKŁAD UŻYCIA:
if __name__ == "__main__":
    job_desc = (
        "Senior Backend Developer (Python/Django). Poszukujemy osoby, która prowadzi "
        "projekty backendowe, optymalizuje zapytania do bazy danych i dba o wysoką jakość kodu."
    )
    user_id = "user_1"
    cv_text = generate_cv(user_id=user_id, job_description=job_desc)
    print(cv_text)
    print("- - - - - - - - - - - - - - - - - - - - - - - - - ")

    evaluation = evaluate_cv_quality(cv_text)
    print("\n📋 Ocena wygenerowanego CV:\n")
    print(evaluation)
    print("- - - - - - - - - - - - - - - - - - - - - - - - - ")

    raw = evaluation["details"]
    # wyciągnij tylko bullet-pointy albo podsumowanie:
    comments = "\n".join(
        line for line in raw.splitlines()
        if line.strip().startswith("- ")
    )
    cv_text = generate_cv(user_id=user_id, job_description=job_desc, additional_comments=comments)
    print(cv_text)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    pdf_file = create_pdf_from_text(cv_text,
                                    wkhtmltopdf_path=os.path.join(base_dir, "htmltopdf", "bin", "wkhtmltopdf.exe"))
    print(f"Wygenerowano PDF: {pdf_file}")
    print("- - - - - - - - - - - - - - - - - - - - - - - - - ")

    evaluation = evaluate_cv_quality(cv_text)
    print("\n📋 Ocena wygenerowanego CV:\n")
    print(evaluation)

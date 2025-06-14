from langchain.prompts import PromptTemplate

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

prompt_text = load_prompt("generate_cv_prompt.txt")
generate_cv_prompt = PromptTemplate(
    input_variables=["context", "input", "additional_comments"],
    template=prompt_text,
)
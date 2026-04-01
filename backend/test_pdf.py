from services.document_processor import extract_text_from_pdf

file_path = "../data/sample.pdf"

text = extract_text_from_pdf(file_path)




print(text[:500])

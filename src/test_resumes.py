from datasets import load_dataset

resumes = load_dataset("datasetmaster/resumes")

print(resumes)
print(resumes["train"].column_names)
print(resumes["train"][0])
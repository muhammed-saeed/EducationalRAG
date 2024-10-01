import os
import tkinter as tk
from tkinter import messagebox, ttk
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()
# Silence Tk deprecation warning
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# OpenAI API key setup
api_key = os.getenv('OPENAI_API_KEY')


# Main folder path
main_folder = "/Users/muhammedsaeed/Desktop/EducationalRAG/Books"
if not os.path.exists(main_folder):
    print(f"Main folder not found: {main_folder}")
    exit(1)

# Function to load topics (folder names)
def load_topics():
    try:
        topics = []
        for folder_name in os.listdir(main_folder):
            folder_path = os.path.join(main_folder, folder_name)
            if os.path.isdir(folder_path):
                topics.append(folder_name)
        print("Topics loaded:", topics)
        return topics
    except Exception as e:
        print("Failed to load topics:", e)
        return []

# Function to load books from a specific topic folder
def load_books_from_topic(topic):
    try:
        books = {}
        topic_folder = os.path.join(main_folder, topic)
        for file_name in os.listdir(topic_folder):
            if file_name.endswith('.pdf'):
                full_path = os.path.join(topic_folder, file_name)
                books[file_name] = full_path
        print(f"Books for {topic} loaded:", books)
        return books
    except Exception as e:
        print(f"Failed to load books for {topic}:", e)
        return {}

# Function to load and process the selected book
def load_document(path):
    try:
        loader = PyMuPDFLoader(path)
        return loader.load()
    except Exception as e:
        print(f"Failed to load document at {path}:", e)
        return None

# GUI for selecting a topic, book, and asking questions
class InteractiveApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EducationalRAG Query System")
        self.geometry("600x700")
        self.initialize_ui()
        print("UI initialized")

    def initialize_ui(self):
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Load available topics
        self.topics = load_topics()

        # Dropdown for topics
        ttk.Label(self.scrollable_frame, text="Select a Topic:").pack(padx=10, pady=5, anchor="w")
        self.topic_var = tk.StringVar(self)
        self.topic_dropdown = ttk.Combobox(self.scrollable_frame, textvariable=self.topic_var, values=self.topics)
        self.topic_dropdown.pack(padx=10, pady=5, fill="x")
        self.topic_dropdown.bind("<<ComboboxSelected>>", self.update_books)

        # Dropdown for books (initially empty)
        ttk.Label(self.scrollable_frame, text="Select a Book:").pack(padx=10, pady=5, anchor="w")
        self.book_var = tk.StringVar(self)
        self.book_dropdown = ttk.Combobox(self.scrollable_frame, textvariable=self.book_var)
        self.book_dropdown.pack(padx=10, pady=5, fill="x")

        # Input for question
        ttk.Label(self.scrollable_frame, text="Enter your question:").pack(padx=10, pady=5, anchor="w")
        self.query_entry = ttk.Entry(self.scrollable_frame)
        self.query_entry.pack(padx=10, pady=5, fill="x")

        # Button to submit the question
        submit_button = ttk.Button(self.scrollable_frame, text="Submit", command=self.process_query)
        submit_button.pack(padx=10, pady=10)

        # Output text box for the response
        ttk.Label(self.scrollable_frame, text="Response:").pack(padx=10, pady=5, anchor="w")
        self.response_text = tk.Text(self.scrollable_frame, height=10, wrap=tk.WORD)
        self.response_text.pack(padx=10, pady=5, fill="both", expand=True)

    def update_books(self, event=None):
        # Load books from the selected topic
        selected_topic = self.topic_var.get()
        self.books = load_books_from_topic(selected_topic)

        # Update the book dropdown with the available books
        self.book_dropdown['values'] = list(self.books.keys())

    def process_query(self):
        # Get the selected book and query
        selected_book = self.book_var.get()
        query = self.query_entry.get()

        if not selected_book:
            messagebox.showwarning("Warning", "Please select a book!")
            return

        if not query:
            messagebox.showwarning("Warning", "Please enter a question!")
            return

        # Load and process the book
        book_path = self.books[selected_book]
        pages = load_document(book_path)

        if pages is None:
            messagebox.showerror("Error", "Failed to load the document.")
            return

        # Split the book into chunks
        text_splitter = CharacterTextSplitter(separator="\n", chunk_size=400, chunk_overlap=150, length_function=len)
        docs = text_splitter.split_documents(pages)

        # Clean the documents
        docs = [remove_ws(d) for d in docs]

        # Create embeddings and FAISS vectorstore
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(docs, embedding=embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={'k': 3})

        # Define the prompt template
        template = """
        You are an information retrieval AI. Format the retrieved information as a text. 
        Use only the context for your answers, do not make up information, your context is coming from a book.
        Only speak in Arabic.
        
        Query: {query}

        {context}
        """

        prompt = ChatPromptTemplate.from_template(template)
        llm = ChatOpenAI(temperature=0.7, model_name="gpt-4")

        # Construct chain
        chain = (
            {"context": retriever, "query": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        # Execute the chain and get response
        response = chain.invoke(query)

        # Display the response in the text box
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, response)

# Function to clean document contents
def remove_ws(d):
    unwanted_chars = ['\n', '\t', '\u0e00', 'Խ', 'đ', '©', '®', '™', 'ҙ', '�']
    for char in unwanted_chars:
        d.page_content = d.page_content.replace(char, '')
    return d

# Run the application
if __name__ == "__main__":
    print("Starting the application...")
    app = InteractiveApp()
    print("Application initialized. Running mainloop...")
    app.mainloop()
    print("Application closed.")

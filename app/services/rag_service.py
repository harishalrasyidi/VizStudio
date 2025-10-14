# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_postgres.vectorstores import PGVector
# from langchain_core.documents import Document
# from app.core.config import settings
# from sqlalchemy import create_engine

# class RAGService:
#     def __init__(self):
#         # Inisialisasi Google Embeddings
#         self.embeddings = GoogleGenerativeAIEmbeddings(
#             model="models/embedding-001",
#             google_api_key=settings.GOOGLE_API_KEY
#         )
        
#         # Buat SQLAlchemy engine untuk koneksi database
#         engine = create_engine(settings.DATABASE_URL)
        
#         # Inisialisasi PGVector dengan parameter yang benar
#         self.vectorstore = PGVector(
#             connection=engine,
#             embedding_function=self.embeddings,
#             collection_name="knowledge_embeddings"
#         )

#     def upsert_knowledge(self, data):
#         doc = Document(
#             page_content=f"{data['term']}: {data['content']}",
#             metadata={
#                 "id": str(data['id']),
#                 "id_datasource": data['id_datasource'],
#                 "entry_type": data['entry_type'],
#                 "term": data['term']
#             }
#         )
#         self.vectorstore.add_documents([doc])

#     def delete_knowledge(self, id):
#         self.vectorstore.delete(ids=[str(id)])

#     def retrieve_relevant_knowledge(self, query: str, id_datasource: int, k: int = 5):
#         filter = {"id_datasource": id_datasource}
#         docs = self.vectorstore.similarity_search(query, k=k, filter=filter)
#         return [doc.page_content for doc in docs]
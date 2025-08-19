# from sentence_transformers import SentenceTransformer
# import faiss
# import numpy as np
# from sqlalchemy.orm import Session
# from app.db.database import SessionLocal, ChatHistory
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)

# # Inisialisasi model embedding
# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
# dimension = 384  # Dimensi vektor dari model ini

# # Inisialisasi FAISS index
# index = faiss.IndexFlatL2(dimension)
# chat_vectors = []  # Untuk menyimpan vektor sementara
# chat_ids = []     # Untuk menyimpan ID pesan

# def get_db_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# def save_chat_to_vector(user_id: str, prompt: str, sql_query: str, analysis: str, db: Session):
#     # Simpan ke database relasional
#     chat = ChatHistory(
#         user_id=user_id,
#         message=prompt,
#         prompt=prompt,
#         sql_query=sql_query,
#         analysis=analysis,
#         timestamp=datetime.now(),
#         edited=False
#     )
#     db.add(chat)
#     db.commit()
#     db.refresh(chat)

#     # Konversi pesan ke vektor
#     message_text = f"{prompt} {analysis}"  # Gabungkan prompt dan analisis
#     embedding = embedding_model.encode([message_text])[0]
#     chat_vectors.append(embedding)
#     chat_ids.append(chat.id)

#     # Tambahkan ke FAISS index
#     if len(chat_vectors) == 1:
#         index = faiss.IndexFlatL2(dimension)  # Inisialisasi ulang jika pertama kali
#     matrix = np.array(chat_vectors).astype('float32')
#     index.add(matrix)

#     return chat.id

# def get_relevant_history(user_id: str, current_prompt: str, db: Session, top_k=3):
#     # Konversi prompt saat ini ke vektor
#     current_embedding = embedding_model.encode([current_prompt])[0].reshape(1, -1).astype('float32')

#     # Cari vektor terdekat di FAISS
#     if len(chat_vectors) == 0:
#         logger.warning("No chat vectors available for search.")
#         return []

#     distances, indices = index.search(current_embedding, top_k)

#     # Ambil data dari database berdasarkan indeks
#     relevant_history = []
#     with db as session:
#         for idx in indices[0]:
#             if 0 <= idx < len(chat_ids):
#                 chat = session.query(ChatHistory).filter(ChatHistory.id == chat_ids[idx]).first()
#                 if chat and chat.user_id == user_id:
#                     relevant_history.append({
#                         "id": chat.id,
#                         "message": chat.message,
#                         "analysis": chat.analysis,
#                         "timestamp": chat.timestamp
#                     })
#     return relevant_history
import os
import logging
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
import settings


# 初始化嵌入模型 (复用之前配置好的 nomic-embed-text)
embedding_model = OllamaEmbeddings(
    model=settings.OLLAMA_EMBED_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    # 本地 Ollama 请求不能经过系统 HTTP/HTTPS 代理，否则可能持续返回 502。
    client_kwargs={"trust_env": False},
)
DB_PATH = "./chroma_rag_db"
logger = logging.getLogger(__name__)


# 把数据存储到语义数据库
def process_and_store_file(file_path, user_id):
     """ 后台任务：解析文件并存入该用户的专属向量库"""

     if file_path.endswith(".pdf"):
         doc = PyPDFLoader(file_path).load()
     elif file_path.endswith(".txt"):
         doc = TextLoader(file_path,encoding="utf-8").load()
     else:
         print("不支持的文件格式")
         return

     doc_spliter = RecursiveCharacterTextSplitter(
         chunk_size=300,
         chunk_overlap=50,
         add_start_index=True
     )
     all_docs = doc_spliter.split_documents(doc)

     collection_name = f"user_{user_id}_docs"

     my_company_collection = Chroma(
         collection_name=collection_name,
         embedding_function=embedding_model,
         persist_directory=DB_PATH
     )

     my_company_collection.add_documents(all_docs)

def retrive_user_from_knowledge(user_id,search_query):
    """供智能体调用的检索工具:只查当前用户的专属知识库"""
    if not search_query or not str(search_query).strip():
        return "用户没有提供可用于知识库检索的具体需求"

    #指定名称
    collection_name = f"user_{user_id}_docs"
    try:
        my_company_collection = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=DB_PATH
        )

        result_docs=my_company_collection.similarity_search(str(search_query),k=2)
        if not result_docs:
            return "未在您的知识库中检索到相关信息"

        return "\n\n".join(f"[您的专属资料]:\n{doc.page_content}"for doc in result_docs)
    except Exception as exc:
        # RAG 是增强能力，不应因 Ollama/Chroma 暂时不可用而阻断核心起名。
        logger.warning("企业知识库检索暂时不可用，已降级为无 RAG 起名：%s", exc)
        return "企业知识库当前暂不可用，请基于用户需求直接完成命名"

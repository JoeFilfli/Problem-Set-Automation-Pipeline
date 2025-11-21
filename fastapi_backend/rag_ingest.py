"""
RAG Ingestion Pipeline - Main Script
Processes all PDFs in sample_materials folder, chunks them semantically,
embeds them, and stores in ChromaDB for retrieval.
"""
import os
from chunker import smart_chunk_without_llm
from pdf_extractor import extract_pdf_text
from vector_store import RAGVectorStore


def process_directory(folder: str, use_llm_chunking: bool = False) -> RAGVectorStore:
    """
    Process all PDF files in a directory.
    
    Args:
        folder: Path to folder containing PDF files
        use_llm_chunking: If True, use LLM-based chunking. If False, use rule-based (default: False)
        
    Returns:
        RAGVectorStore instance with all documents processed
    """
    print(f"[INIT] Creating {'LLM' if use_llm_chunking else 'Rule-Based'} Chunker and Vector Store...")
    vs = RAGVectorStore()
    
    openai_calls = {"chunking": 0, "embedding": 0}

    for filename in os.listdir(folder):
        if not filename.lower().endswith(".pdf"):
            continue

        path = os.path.join(folder, filename)
        doc_id = filename

        print(f"\n=== Processing {filename} ===")
        
        # Skip if already processed
        if vs.document_exists(doc_id):
            print(f" → ⚠ Already ingested, skipping...")
            continue
        
        text = extract_pdf_text(path)
        print(f" → Extracted {len(text)} characters")

        # Choose chunking strategy
        print(f" → Starting {'LLM-based' if use_llm_chunking else 'rule-based'} chunking...")
        if use_llm_chunking:
            from chunker import LLMChunker
            chunker = LLMChunker()
            chunks = chunker.chunk_with_splitting(text)
        else:
            chunks = smart_chunk_without_llm(text, max_size=2000)
        
        print(f" → Created {len(chunks)} chunks")
        
        print(f" → Storing chunks in vector DB...")
        for i, ch in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            vs.add_chunk(ch, doc_id, chunk_id)
            openai_calls["embedding"] += 1

        print(f" → ✓ All {len(chunks)} chunks stored in vector DB")

    print(f"\n{'='*60}")
    print(f"All documents processed successfully!")
    print(f"Total OpenAI API calls: ~{openai_calls['embedding']} (embeddings only)")
    print(f"Note: Chunking calls vary based on document splitting")
    print(f"{'='*60}\n")
    return vs


def test_rag(vs: RAGVectorStore):
    """
    Test full RAG pipeline: retrieve relevant chunks and generate answers using OpenAI.
    
    Args:
        vs: RAGVectorStore instance to query
    """
    from openai import OpenAI
    client = OpenAI()
    
    # Get some topics from the actual course materials for testing
    all_docs = vs.get_all_documents()
    sample_doc = all_docs[0] if all_docs else None
    
    test_queries = [
        {
            "query": "What are the main topics covered in this course?",
            "description": "Course Overview"
        },
        {
            "query": "What are the key formulas or concepts?",
            "description": "Key Concepts"
        },
        {
            "query": "What are the course learning objectives?",
            "description": "Learning Objectives"
        },
        {
            "query": "Can you explain the main principles?",
            "description": "Core Principles"
        },
        {
            "query": "What examples are provided in the materials?",
            "description": "Examples and Applications"
        }
    ]
    
    print("\n" + "="*70)
    print("RAG PIPELINE TESTING (Retrieval + Generation)")
    print("="*70)
    
    for idx, test in enumerate(test_queries, 1):
        print(f"\n[TEST {idx}/{len(test_queries)}] {test['description']}")
        print(f"Query: \"{test['query']}\"")
        print("-" * 70)
        
        # Retrieve relevant chunks
        print("   [Retrieval] Searching vector DB...")
        results = vs.query(test['query'], top_k=4)
        
        if not results["documents"][0]:
            print("⚠ No results found!")
            continue
        
        # Show retrieved sources
        print(f"   [Retrieval] ✓ Found {len(results['documents'][0])} relevant chunks")
        for i, meta in enumerate(results["metadatas"][0], 1):
            print(f"      • {meta['doc_id']} - {meta['summary'][:60]}...")
        
        # Build context from retrieved chunks
        context = "\n\n".join([
            f"[Source: {meta['doc_id']}]\n{doc}"
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ])
        
        # Generate answer using OpenAI
        print(f"\n   [Generation] Sending to OpenAI (gpt-4o-mini)...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful teaching assistant. Answer questions based on the provided course materials. If the context doesn't contain enough information, say so. Use appropriate notation (mathematical, code, etc.) when relevant. Always cite your sources by referencing the document names in your answer."
                },
                {
                    "role": "user",
                    "content": f"Context from course materials:\n\n{context}\n\nQuestion: {test['query']}\n\nProvide a clear, concise answer based on the context above. Include references to which documents you used."
                }
            ],
            temperature=0.3,
        )
        
        answer = response.choices[0].message.content
        
        # Extract unique sources used
        sources_used = list(set([meta['doc_id'] for meta in results["metadatas"][0]]))
        
        print(f"   [Generation] ✓ Answer received\n")
        print("ANSWER:")
        print("-" * 70)
        print(answer)
        print("\n" + "-" * 70)
        print(f"Sources: {', '.join(sources_used)}")
        print()
    
    print("="*70)
    print("Testing complete!")
    print("="*70)


if __name__ == "__main__":
    folder = r"sample_materials"
    vs = process_directory(folder)
    test_rag(vs)

"""
Diagnostic tool to inspect chunks for any document in the vector store.
"""
from vector_store import RAGVectorStore
from pdf_extractor import extract_pdf_text
import json


def inspect_document_chunks(doc_id: str):
    """
    Inspect all chunks for a specific document.
    
    Args:
        doc_id: Document identifier (e.g., 'INDE301_Ch1_Notes_24.pdf')
    """
    vs = RAGVectorStore()
    
    print(f"\n{'='*80}")
    print(f"CHUNK INSPECTION: {doc_id}")
    print(f"{'='*80}\n")
    
    # Check if document exists
    if not vs.document_exists(doc_id):
        print(f"❌ Document '{doc_id}' not found in vector store!")
        print("\nAvailable documents:")
        for doc in vs.get_all_documents():
            print(f"  • {doc}")
        return
    
    # Get all chunks for this document
    results = vs.get_chunks_for_document(doc_id)
    
    num_chunks = len(results['ids'])
    print(f"📊 Total chunks: {num_chunks}")
    print(f"{'='*80}\n")
    
    if num_chunks == 0:
        print("⚠️ No chunks found!")
        return
    
    # Analyze each chunk
    total_chars = 0
    for i, (chunk_id, doc_text, metadata) in enumerate(zip(
        results['ids'],
        results['documents'],
        results['metadatas']
    ), 1):
        chunk_len = len(doc_text)
        total_chars += chunk_len
        
        print(f"CHUNK {i}/{num_chunks}")
        print(f"-"*80)
        print(f"ID: {chunk_id}")
        print(f"Length: {chunk_len} characters")
        print(f"Start Index: {metadata['start']}")
        print(f"End Index: {metadata['end']}")
        print(f"Topics: {metadata['topics']}")
        print(f"\nSummary:")
        print(f"  {metadata['summary']}")
        print(f"\nFirst 300 characters:")
        print(f"  {doc_text[:300]}...")
        print(f"\nLast 200 characters:")
        print(f"  ...{doc_text[-200:]}")
        print(f"\n{'='*80}\n")
    
    print(f"📈 STATISTICS")
    print(f"-"*80)
    print(f"Total chunks: {num_chunks}")
    print(f"Total characters across all chunks: {total_chars:,}")
    print(f"Average chunk size: {total_chars // num_chunks:,} characters")
    print(f"Min chunk size: {min(len(d) for d in results['documents']):,} characters")
    print(f"Max chunk size: {max(len(d) for d in results['documents']):,} characters")
    print(f"{'='*80}\n")


def inspect_original_pdf(pdf_path: str):
    """
    Inspect the original PDF before chunking.
    
    Args:
        pdf_path: Path to the PDF file
    """
    print(f"\n{'='*80}")
    print(f"PDF INSPECTION: {pdf_path}")
    print(f"{'='*80}\n")
    
    try:
        text = extract_pdf_text(pdf_path)
        
        print(f"📄 PDF Text Extraction")
        print(f"-"*80)
        print(f"Total characters: {len(text):,}")
        print(f"Total lines: {len(text.splitlines()):,}")
        print(f"Total words (approx): {len(text.split()):,}")
        
        print(f"\nFirst 500 characters:")
        print(f"{text[:500]}")
        print(f"\n...")
        print(f"\nLast 500 characters:")
        print(f"...{text[-500:]}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")


def compare_all_documents():
    """Compare chunk counts across all documents."""
    vs = RAGVectorStore()
    
    print(f"\n{'='*80}")
    print(f"ALL DOCUMENTS COMPARISON")
    print(f"{'='*80}\n")
    
    all_docs = vs.get_all_documents()
    
    doc_stats = []
    for doc_id in all_docs:
        results = vs.get_chunks_for_document(doc_id)
        num_chunks = len(results['ids'])
        total_chars = sum(len(d) for d in results['documents'])
        
        doc_stats.append({
            'doc_id': doc_id,
            'num_chunks': num_chunks,
            'total_chars': total_chars,
            'avg_chunk_size': total_chars // num_chunks if num_chunks > 0 else 0
        })
    
    # Sort by number of chunks
    doc_stats.sort(key=lambda x: x['num_chunks'])
    
    print(f"{'Document':<50} {'Chunks':<10} {'Total Chars':<15} {'Avg Chunk Size'}")
    print(f"-"*90)
    
    for stat in doc_stats:
        print(f"{stat['doc_id']:<50} {stat['num_chunks']:<10} {stat['total_chars']:<15,} {stat['avg_chunk_size']:,}")
    
    print(f"\n{'='*80}\n")


def test_rechunk(pdf_path: str, doc_id: str):
    """
    Test chunking on a specific PDF to see what's happening.
    
    Args:
        pdf_path: Path to the PDF file
        doc_id: Document identifier
    """
    from chunker import LLMChunker
    
    print(f"\n{'='*80}")
    print(f"TEST RECHUNKING: {doc_id}")
    print(f"{'='*80}\n")
    
    # Extract text
    print("[1] Extracting PDF text...")
    text = extract_pdf_text(pdf_path)
    print(f"    ✓ Extracted {len(text):,} characters\n")
    
    # Chunk the text
    print("[2] Starting semantic chunking (with splitting)...")
    chunker = LLMChunker()
    chunks = chunker.chunk_with_splitting(text, max_chars=15000, overlap=500, max_size=1400)
    print(f"    ✓ Created {len(chunks)} chunks\n")
    
    # Display chunk details
    print("[3] Chunk Details:")
    print(f"-"*80)
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i}: {len(chunk.formatted)} chars | Topics: {', '.join(chunk.topics)}")
        print(f"  Summary: {chunk.summary[:80]}...")
        print()
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    import sys
    
    # Default: compare all documents
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python inspect_chunks.py compare              # Compare all documents")
        print("  python inspect_chunks.py inspect <doc_id>     # Inspect specific document")
        print("  python inspect_chunks.py pdf <path>           # Inspect PDF before chunking")
        print("  python inspect_chunks.py rechunk <path> <id>  # Test rechunking")
        print()
        compare_all_documents()
    
    elif sys.argv[1] == "compare":
        compare_all_documents()
    
    elif sys.argv[1] == "inspect" and len(sys.argv) > 2:
        inspect_document_chunks(sys.argv[2])
    
    elif sys.argv[1] == "pdf" and len(sys.argv) > 2:
        inspect_original_pdf(sys.argv[2])
    
    elif sys.argv[1] == "rechunk" and len(sys.argv) > 3:
        test_rechunk(sys.argv[2], sys.argv[3])
    
    else:
        print("Invalid arguments. Run without arguments to see usage.")

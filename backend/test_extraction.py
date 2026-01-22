# Test Document Extraction
from internal_assistant_core import blob_container
from rag_modul import _extract_text_with_docint
import json

def test_document_extraction(blob_name: str):
    """Test ekstraksi dokumen dan tampilkan hasilnya"""
    try:
        # Download dokumen
        blob_client = blob_container.get_blob_client(blob_name)
        content_bytes = blob_client.download_blob().readall()
        
        # Ekstraksi dengan Document Intelligence
        doc_data = _extract_text_with_docint(content_bytes)
        
        # Save hasil ke file JSON
        filename = f"ekstraksi_{blob_name.replace('/', '_').replace('.pdf', '')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"Dokumen: {blob_name}")
        print(f"Sections: {len(doc_data['sections'])}")
        print(f"Tables: {len(doc_data['raw_tables'])}")
        print(f"Saved to: {filename}")
        
        # Show first few sections
        for i, section in enumerate(doc_data['sections'][:3]):
            print(f"\nSection {i+1}: {section['header']}")
            print(f"  Type: {section['type']}")
            print(f"  Content parts: {len(section['content_parts'])}")
            print(f"  Total tokens: {section['total_tokens']}")
            
        return doc_data
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def list_available_documents():
    """List semua dokumen yang ada di blob storage"""
    try:
        print("📂 Available documents:")
        blob_list = list(blob_container.list_blobs())
        
        if not blob_list:
            print("❌ No documents found in blob storage")
            return []
            
        for i, blob in enumerate(blob_list, 1):
            print(f"  {i}. {blob.name}")
            
        return [blob.name for blob in blob_list]
        
    except Exception as e:
        print(f"Error listing documents: {e}")
        return []

if _name_ == "_main_":
    # List available documents first
    docs = list_available_documents()
    
    if docs:
        # Test dengan dokumen pertama yang ada
        print(f"\n🧪 Testing extraction with: {docs[0]}")
        test_document_extraction(docs[0])
    else:
        print("No documents to test with")
"""
RootSight — Build Memory Index

Seeds the FAISS vector store with past incident embeddings.
Run this once before launching the Streamlit UI.

Usage:
    python scripts/build_memory_index.py
"""

import sys
import json
from pathlib import Path

# Fix Unicode printing issues on Windows terminals
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SEED_DIR, settings
from src.services.vector_store import vector_store
from src.integrations.embedding_client import embedding_client, EMBEDDING_MODEL
from src.utils.logger import get_logger

logger = get_logger("scripts.build_memory_index")


def main():
    print("\n" + "=" * 60)
    print("  RootSight — Building Memory Index")
    print("=" * 60)

    if not settings.has_gemini_key:
        print("\n⚠️  No Gemini API key found.")
        print("   Set GEMINI_API_KEY in your .env file to use real embeddings.")
        print("   Skipping index build — memory agent will report 'no historical data'.")
        return

    if not embedding_client.is_available:
        print("\n❌  Embedding client not available. Check your GEMINI_API_KEY.")
        return

    # Load all seed incidents
    incidents_dir = SEED_DIR / "sample_incidents"
    if not incidents_dir.exists():
        print(f"\n❌  Seed incidents not found at {incidents_dir}")
        return

    incident_files = list(incidents_dir.glob("*.json"))
    if not incident_files:
        print("\n❌  No incident files found in seed directory")
        return

    print(f"\n📂  Found {len(incident_files)} seed incidents")

    incidents = []
    for f in incident_files:
        with open(f) as fh:
            data = json.load(fh)
        incidents.append(data)
        print(f"   ✓ {data['incident_id']}: {data['title']}")

    # Generate embeddings
    print(f"\n🧠  Generating embeddings via {EMBEDDING_MODEL}...")
    texts = []
    for inc in incidents:
        text = (
            f"Service: {inc['service']}. "
            f"Title: {inc['title']}. "
            f"Root cause: {inc['root_cause']}. "
            f"Summary: {inc['summary']}"
        )
        texts.append(text)

    try:
        embeddings = embedding_client.embed_batch(texts)
        print(f"   ✓ Generated {len(embeddings)} embeddings")
    except Exception as e:
        print(f"\n❌  Embedding generation failed: {e}")
        return

    # Build metadata list
    metadata = []
    for inc in incidents:
        metadata.append({
            "incident_id": inc["incident_id"],
            "title": inc["title"],
            "service": inc["service"],
            "severity": inc.get("severity", "P3"),
            "root_cause": inc["root_cause"],
            "resolution": inc["resolution"],
            "similarity_reason": inc.get("similarity_reason", ""),
            "summary": inc["summary"],
        })

    # Build and save FAISS index
    print(f"\n💾  Building FAISS index...")
    vector_store.build_index(embeddings, metadata)

    index_path = settings.FAISS_INDEX_PATH
    metadata_path = settings.FAISS_METADATA_PATH
    vector_store.save(index_path, metadata_path)

    print(f"\n✅  Memory index built successfully!")
    print(f"   Index:    {index_path}")
    print(f"   Metadata: {metadata_path}")
    print(f"   Incidents: {vector_store.count}")
    print("\n" + "=" * 60)
    print("  Ready! Run: streamlit run ui/app.py")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

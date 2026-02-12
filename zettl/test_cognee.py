#!/usr/bin/env python3
"""Quick test to verify Cognee + Vertex AI configuration."""

import asyncio
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print config for debugging
print("=== Configuration ===")
print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL')}")
print(f"VERTEX_PROJECT: {os.getenv('VERTEX_PROJECT')}")
print(f"VERTEX_LOCATION: {os.getenv('VERTEX_LOCATION')}")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'not set (using ADC)')}")
print()


async def test_cognee():
    import cognee

    print("=== Testing Cognee ===")

    # Add a simple test document
    test_content = "Python is a programming language created by Guido van Rossum."
    print(f"Adding test content: {test_content[:50]}...")

    await cognee.add([test_content], dataset_name="test_dataset")
    print("✓ cognee.add() succeeded")

    # Process into knowledge graph
    print("Running cognify...")
    await cognee.cognify(["test_dataset"])
    print("✓ cognee.cognify() succeeded")

    # Test search
    print("Testing search...")
    from cognee.modules.search.types import SearchType
    results = await cognee.search(
        query_type=SearchType.CHUNKS,
        query_text="Python programming",
        datasets=["test_dataset"]
    )
    print(f"✓ Search returned {len(results)} results")

    print("\n=== All tests passed! ===")


if __name__ == "__main__":
    asyncio.run(test_cognee())

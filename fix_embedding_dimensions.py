#!/usr/bin/env python3
"""
Script to fix embedding dimension mismatch in Mini RAG application
This script resets the vector database to use consistent embedding dimensions
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000/api/v1"
PROJECT_ID = "1"

def check_server():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/debug/config", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running on port 5000")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def get_config():
    """Get current configuration"""
    try:
        response = requests.get(f"{BASE_URL}/debug/config")
        if response.status_code == 200:
            config = response.json()
            print("\n📊 Current Configuration:")
            print("=" * 50)
            
            # Check embedding client
            embedding = config.get('embedding_client', {})
            print(f"Embedding Client: {'✅' if embedding.get('available') else '❌'}")
            if embedding.get('available'):
                print(f"  Model ID: {embedding.get('model_id', 'Not set')}")
                print(f"  Embedding Size: {embedding.get('embedding_size', 'Not set')}")
                print(f"  Client Type: {embedding.get('client_type', 'Unknown')}")
            
            # Check generation client
            generation = config.get('generation_client', {})
            print(f"\nGeneration Client: {'✅' if generation.get('available') else '❌'}")
            if generation.get('available'):
                print(f"  Model ID: {generation.get('model_id', 'Not set')}")
                print(f"  Client Type: {generation.get('client_type', 'Unknown')}")
            
            # Check vector DB
            vectordb = config.get('vectordb_client', {})
            print(f"\nVector DB Client: {'✅' if vectordb.get('available') else '❌'}")
            if vectordb.get('available'):
                print(f"  Client Type: {vectordb.get('client_type', 'Unknown')}")
            
            return config
        else:
            print(f"❌ Failed to get configuration: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting configuration: {e}")
        return None

def get_collection_info():
    """Get current collection info"""
    try:
        response = requests.get(f"{BASE_URL}/nlp/index/info/{PROJECT_ID}")
        if response.status_code == 200:
            info = response.json()
            print(f"\n📋 Collection Info for Project {PROJECT_ID}:")
            print("=" * 50)
            collection_info = info.get('collection_info', {})
            print(f"Collection exists: {collection_info.get('exists', False)}")
            if collection_info.get('exists'):
                print(f"Vector count: {collection_info.get('vectors_count', 0)}")
                print(f"Indexed vectors: {collection_info.get('indexed_vectors_count', 0)}")
            return info
        else:
            print(f"❌ Failed to get collection info: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting collection info: {e}")
        return None

def reset_vector_database():
    """Reset the vector database with do_reset=1"""
    print(f"\n🔄 Resetting vector database for project {PROJECT_ID}...")
    try:
        response = requests.post(f"{BASE_URL}/nlp/index/push/{PROJECT_ID}", 
                               json={"do_reset": 1})
        if response.status_code == 200:
            result = response.json()
            print("✅ Vector database reset successfully")
            print(f"  Signal: {result.get('signal', 'N/A')}")
            print(f"  Inserted items: {result.get('inserted_items_count', 0)}")
            return True
        else:
            print(f"❌ Failed to reset vector database: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error resetting vector database: {e}")
        return False

def test_answer():
    """Test the answer endpoint"""
    print(f"\n🤖 Testing answer endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/nlp/index/answer/{PROJECT_ID}", 
                               json={"text": "What is the product table?", "limit": 5})
        if response.status_code == 200:
            result = response.json()
            print("✅ Answer endpoint working!")
            answer = result.get('answer', 'No answer')
            print(f"  Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            return True
        else:
            print(f"❌ Answer endpoint failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing answer endpoint: {e}")
        return False

def main():
    print("🔧 Mini RAG Embedding Dimension Fix Tool")
    print("=" * 50)
    
    # Check if server is running
    if not check_server():
        print("\n💡 Please start your server first:")
        print("   uvicorn main:app --reload")
        return
    
    # Get current configuration
    config = get_config()
    if not config:
        return
    
    # Get collection info
    collection_info = get_collection_info()
    
    # Check if we need to reset
    embedding_size = config.get('embedding_client', {}).get('embedding_size')
    if not embedding_size:
        print("\n❌ Embedding size not configured. Please check your .env file.")
        return
    
    print(f"\n🎯 Target embedding size: {embedding_size}")
    
    # Reset vector database
    if reset_vector_database():
        print("\n✅ Vector database reset completed!")
        
        # Test the answer endpoint
        if test_answer():
            print("\n🎉 Everything is working correctly!")
        else:
            print("\n⚠️ Vector database reset but answer endpoint still has issues.")
    else:
        print("\n❌ Failed to reset vector database.")

if __name__ == "__main__":
    main()

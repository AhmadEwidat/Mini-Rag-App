#!/usr/bin/env python3
"""
Test script for the Mini RAG application workflow
This script demonstrates the complete process from file upload to getting answers
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api/v1"
PROJECT_ID = "1"

def test_workflow():
    print("🚀 Starting Mini RAG Test Workflow")
    print("=" * 50)
    
    # Step 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/debug/config")
        if response.status_code == 200:
            print("✅ Server is running")
            config = response.json()
            print(f"📊 Configuration Status:")
            for service, status in config.items():
                print(f"   {service}: {'✅' if status['available'] else '❌'}")
        else:
            print("❌ Server is not responding properly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:5000")
        return
    
    print("\n" + "=" * 50)
    
    # Step 2: Upload test file
    print("📁 Step 1: Uploading test document...")
    try:
        with open("test_document.txt", "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/data/upload/{PROJECT_ID}", files=files)
            
        if response.status_code == 200:
            print("✅ File uploaded successfully")
            upload_data = response.json()
            print(f"   File ID: {upload_data.get('file_id', 'N/A')}")
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except FileNotFoundError:
        print("❌ test_document.txt not found. Please create it first.")
        return
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Step 3: Process file into chunks
    print("⚙️ Step 2: Processing file into chunks...")
    try:
        process_data = {
            "chunk_size": 500,
            "overlap_size": 100,
            "do_reset": 0
        }
        response = requests.post(f"{BASE_URL}/data/process/{PROJECT_ID}", 
                               json=process_data)
        
        if response.status_code == 200:
            print("✅ File processed successfully")
            process_result = response.json()
            print(f"   Signal: {process_result.get('signal', 'N/A')}")
        else:
            print(f"❌ File processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Step 4: Index chunks into vector database
    print("🔍 Step 3: Indexing chunks into vector database...")
    try:
        index_data = {"do_reset": 0}
        response = requests.post(f"{BASE_URL}/nlp/index/push/{PROJECT_ID}", 
                               json=index_data)
        
        if response.status_code == 200:
            print("✅ Chunks indexed successfully")
            index_result = response.json()
            print(f"   Signal: {index_result.get('signal', 'N/A')}")
            print(f"   Inserted items: {index_result.get('inserted_items_count', 'N/A')}")
        else:
            print(f"❌ Indexing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error indexing chunks: {e}")
        return
    
    print("\n" + "=" * 50)
    
    # Step 5: Test the answer endpoint
    print("🤖 Step 4: Testing RAG answer endpoint...")
    test_queries = [
        "What is the product table?",
        "What fields are in the product table?",
        "What are the relationships of the product table?",
        "What indexes are created on the product table?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: {query}")
        try:
            answer_data = {
                "text": query,
                "limit": 5
            }
            response = requests.post(f"{BASE_URL}/nlp/index/answer/{PROJECT_ID}", 
                                   json=answer_data)
            
            if response.status_code == 200:
                print("   ✅ Answer received successfully")
                answer_result = response.json()
                answer = answer_result.get('answer', 'No answer provided')
                print(f"   📝 Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            else:
                print(f"   ❌ Answer failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error getting answer: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test workflow completed!")

if __name__ == "__main__":
    test_workflow()

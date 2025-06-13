from pymongo import MongoClient
import json
from pprint import pprint

def check_mongo_structure():
    client = MongoClient("mongodb://localhost:27017")
    db = client['aicounsel']
    collection = db['conversations']
    
    # 모든 컬렉션 이름 출력
    print("데이터베이스의 모든 컬렉션:")
    print(db.list_collection_names())
    
    # 첫 번째 문서 확인
    first_doc = collection.find_one()
    if first_doc:
        print("\n첫 번째 문서의 모든 키:")
        print(list(first_doc.keys()))
        
        print("\n첫 번째 문서 전체 내용:")
        pprint(first_doc)
    else:
        print("컬렉션에 문서가 없습니다.")
    
    # 문서 수 확인
    doc_count = collection.count_documents({})
    print(f"\n총 문서 수: {doc_count}")
    
    client.close()

if __name__ == "__main__":
    check_mongo_structure() 

import sys
import os
sys.path.append(os.path.abspath("src"))

from psychrag.data.database import get_session
from psychrag.data.models import Query, Result

def check_data(query_id):
    print("Checking database...")
    try:
        with get_session() as session:
            query = session.query(Query).filter(Query.id == query_id).first()
            if not query:
                print(f"Query {query_id} NOT FOUND")
            else:
                print(f"Query {query_id} FOUND: {query.original_query}")
                results = session.query(Result).filter(Result.query_id == query_id).all()
                print(f"Found {len(results)} results for query {query_id}")
                for r in results:
                    print(f"  - Result {r.id}: {r.response_text[:30]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data(7)

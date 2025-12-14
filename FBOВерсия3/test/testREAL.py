# test_direct_api.py
import requests
import json
from datetime import datetime, timezone, timedelta


def test_direct_ozon_api():
    client_id = "2115535"
    api_key = "5dfb875a3"

    headers = {
        "Client-Id": client_id,
        "Api-Key": api_key,
        "Content-Type": "application/json"
    }

    period_to = datetime.now(timezone.utc)
    period_from = period_to - timedelta(days=7)

    # Форматируем даты
    since_str = period_from.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    to_str = period_to.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    data = {
        "dir": "ASC",
        "filter": {
            "since": since_str,
            "to": to_str
        },
        "limit": 10,
        "offset": 0,
        "translit": True,
        "with": {
            "analytics_data": True,
            "financial_data": True
        }
    }

    print("Testing direct Ozon API call...")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(
            "https://api-seller.ozon.ru/v2/posting/fbo/list",
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"\nStatus: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nParsed response:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])

            if "result" in result:
                postings = result["result"]
                if isinstance(postings, list):
                    print(f"\n✅ Found {len(postings)} postings")
                    if postings:
                        print(f"First posting: {postings[0].get('posting_number')}")
                else:
                    print(f"\n⚠️ Result is not a list. Type: {type(postings)}")
            else:
                print(f"\n❌ No 'result' key. Keys: {list(result.keys())}")
        else:
            print(f"\n❌ Error: {response.text}")

    except Exception as e:
        print(f"\n❌ Exception: {e}")


if __name__ == "__main__":
    test_direct_ozon_api()
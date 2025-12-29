import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8002"
EXAM_ID = "test-exam-verification"

def run_test():
    print(f"Testing against {BASE_URL}...")

    # 1. セッション作成 (GET /sessions)
    print("\n1. Creating/Fetching Session...")
    import time
    for i in range(5):
        try:
            res = requests.get(f"{BASE_URL}/api/interview/sessions/{EXAM_ID}")
            res.raise_for_status()
            break
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            time.sleep(2)
    else:
        print("Failed to connect after 5 attempts.")
        return

    session = res.json()

    # 2. チャット送信 (POST /chat) - 履歴を作るため
    print("\n2. Sending Chat Message...")
    try:
        # ストリーミングなので少し特殊ですが、リクエストが通るかだけ確認
        res = requests.post(
            f"{BASE_URL}/api/interview/chat/{EXAM_ID}",
            json={"message": "物流業界の2024年問題について、配送ルート最適化の観点で論文を書きたいです。"}
        )
        res.raise_for_status()
        print("Chat request successful (Stream started)")
        # ストリームの中身は今回は無視
    except Exception as e:
        print(f"Failed to chat: {e}")
        return

    # 3. 設計書生成 (POST /generate)
    print("\n3. Generating Design Proposal...")
    try:
        res = requests.post(f"{BASE_URL}/api/interview/generate/{EXAM_ID}")
        if res.status_code == 500:
            print("Server Error (500). Check logs.")
            print(res.text)
            return
        
        res.raise_for_status()
        proposal = res.json()
        
        print("\n--- Generated Proposal ---")
        print(json.dumps(proposal, indent=2, ensure_ascii=False))
        print("--------------------------")
        
        if "theme" in proposal and "structure" in proposal:
            print("\nSUCCESS: Valid proposal generated!")
        else:
            print("\nWARNING: Proposal structure might be invalid.")

    except Exception as e:
        print(f"Failed to generate: {e}")

if __name__ == "__main__":
    run_test()

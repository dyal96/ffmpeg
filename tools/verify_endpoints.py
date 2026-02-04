import requests
import os

BASE_URL = "http://127.0.0.1:5000"

def test_upload():
    print("Testing Upload...")
    file_path = "test_upload.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("test content")
            
    with open(file_path, "rb") as f:
        files = {"file": f}
        try:
            r = requests.post(f"{BASE_URL}/api/upload", files=files)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}")
            if r.status_code == 200 and "path" in r.json():
                print("✅ Upload Success")
                return r.json()["path"]
            else:
                print("❌ Upload Failed")
        except Exception as e:
            print(f"❌ Upload Error: {e}")
    return None

def test_ytdl_command_dry_run():
    # We can't easily check the internal command construction without modifying the webui to return it,
    # but we can check if it accepts the request and starts a job.
    print("\nTesting yt-dlp start...")
    payload = {
        "url": "https://www.youtube.com/watch?v=BaW_jenozKc", # Dummy URL
        "quality": "best",
        "format": "mp4",
        "subs": True,
        "thumbnail": True
    }
    
    try:
        r = requests.post(f"{BASE_URL}/api/tools/ytdl/run", json=payload)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        if r.status_code == 200 and "job_id" in r.json():
            print("✅ yt-dlp Job Started")
            return r.json()["job_id"]
        else:
            print("❌ yt-dlp Job Fail")
    except Exception as e:
        print(f"❌ yt-dlp Request Error: {e}")
        
    return None

if __name__ == "__main__":
    test_upload()
    test_ytdl_command_dry_run()

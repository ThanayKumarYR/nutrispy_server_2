def query(filename):
    import requests
    import os
    API_URL = "https://api-inference.huggingface.co/models/nateraw/food"
    headers = {"Authorization":os.getenv("HUGGING_FACE_AUTHORIZATION")}
    with open(filename, "rb") as f:
        data = f.read()
    response = requests.post(API_URL, headers=headers, data=data)
    return response.json()[0]['label']

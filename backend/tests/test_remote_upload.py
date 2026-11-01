import urllib.request
import json

boundary = '----WebKitBoundary123'
body = (
    b'--' + boundary.encode() + b'\r\n'
    b'Content-Disposition: form-data; name="file"; filename="test_sample.mp4"\r\n'
    b'Content-Type: video/mp4\r\n\r\n'
    b'header-video-sample-bytes\r\n'
    b'--' + boundary.encode() + b'--\r\n'
)

req = urllib.request.Request(
    'https://autovision-ai-0xcx.onrender.com/api/upload',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

with urllib.request.urlopen(req) as res:
    data = json.loads(res.read().decode())
    print("Upload result from Render:")
    print(json.dumps(data, indent=2))

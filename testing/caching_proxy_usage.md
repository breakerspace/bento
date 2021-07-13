This is a caching proxy server. It is meant to be run on a Bento server and it accepts requests from any web browser, fetches the content, and caches the result, and then sends it back to the client. The motivation for this is that browsing hidden services is often very slow because of latencies on the Tor network. However, with this caching proxy server, only the first time browsing a hidden service will be slow because all subsequent requests to the same hidden service will be much faster. This caching proxy server also works for normal websites as well. The caching proxy server currently works with any browser (including the Tor Browser) and works when the Bento server is run *without* sgx. Support for sgx is on the way.

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

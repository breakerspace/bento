#### Setup: 
client <-> proxy.py <-> [Tor network] <-> bento server <-> webserver   

The client is any application that would like to access a remote webserver
(cURL, a web browsers, etc.)

- make sure a bento server is running 
- start the proxy:   

```
./proxy.py
```

By default, the proxy listens on 127.0.0.1:9011 and connects to a Bento
server at 127.0.0.1:8888; each of these can specified on the command-line
(run `./proxy.py -h` for the usage details).


Using cURL (simple GET request):  
	`curl -v -4 --socks5 127.0.0.1:9011 <ip|domain>`  
Example:   
	`curl -v -4 --socks5 127.0.0.1:9011 http://example.com/?q=ultrasurf`  

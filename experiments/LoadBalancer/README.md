# Load Balancer for Tor

## About: Scripts

### load_balancer.func 

By default the load balancer uses 4 replicas with a max of 2 clients per replica.

The load balancer waits for all replicas to first connect.  It next receives
updates from each replica, and based on that, signals them to launch Tor (scale
up), kill Tor (scale down), or do nothing (if the replica it catering
to a client). 

### replica.py

Usage:

```
python3 replica.py <IP of loadbalancer>
```

A replica connects to the ```load_balancer.func``` Bento function. Based on the
signal from the load balancer, the replica launches a Tor instance, kills it,
or does nothing and just caters to existing client. 


### master_client.py:

The master client is effectively a fence for the purpose of evaluating the load
balancer with a configurable number of concurrent clients: a set of clients
connect to the master client; once all clients have connected, the master
client sends them a `READY` message saying that they may now connect to the
hidden service.  The dispatching of the `READY` message may be based on the
Poisson arrival rate.

Usage: 

```
python3 master_client.py <no. of clients>
```


### client.py:

Usage: 

```python3 client.py <IP of master_client.py>```

The client is a web agent that accesses the hidden service.  The client first
connects to ```master_client.py``` and then waits for the `READY` signal.  Once
the `READY` signal is received, the client launches an Onion proxy, and then
accesses the hidden service via the proxy.  The hidden service URL is currently
hardcoded in the script.


## Setup

### Setup the replicas
* Choose about 4-5 Replica machines (like Amazon AWS instances) and install [Tor](https://barc-purdue.github.io/BentoDocs/services.html) on them. 
* Create a sample Onion Service on the first [Replica](https://barc-purdue.github.io/BentoDocs/services.html). 
* Test the hidden service by accessing the .onion address (stored in ```/usr/local/var/lib/tor/hidden_service/hostname```) through a Tor Browser.
* Setup other Replicas. All the replicas should host the same onion service. We can achieve this by letting the replicas share the same private key. For this, create a ```bento``` directory on all the replicas and copy ```run_tor.py``` and ```replica.py```. Further, copy the same hostname and private key of the created onion service in the same ```bento``` directory. 

```
mkdir bento
cp /usr/local/var/lib/tor/hidden_service/hs_ed25519_secret_key bento/
cp /usr/local/var/lib/tor/hidden_service/hostname bento/
```
* In the ```replica.py``` change the default port number of the ```port = 12345```. This port number specifies the port used by ```load_balancer.func```.

This completes the replica setup. 


### Setup the Load Balancer

First upload and execute the loadbalancer Bento function (load_balancer.func)
using driver.py. Next, run the ```replica.py``` scripts on different
servers that act as a replica to the repective Onion Service.     

* Start the Bento Server. Navigate to ```bento/server/``` and run:  
`mkdir sessions; mkdir functions`   
`python3.6 runserver.py` 

* Start the client. Navigate to ```bento/experiments/LoadBalancer/``` and run:

`python3.6 driver.py <host> <port>` which uploads and executes the load balancer Bento function on the server. 

* Connect replicas with the running load balancer on the Bento Server. Navigate to ```bento/``` and run:
```python3 replica.py <IP of the Bento Server>```
The Load Balancer is up and running. 

## Experimentation
* Setup the clients: We used 13 AWS instances to set up the clients. The idea is that client (```client.py```) visits the onion service after an interval (can be random or fixed) and downloads a fixed size file, which is controlled by the ```master_client.py``` (which runs on a separate instance). We then assess the bandwidth available for each client.
* Setup the Onion Service. Upload a fixed size file to the Onion Service, which the clients can download for testing. 
* Change the IP address, port number, onion address, number of clients, client intervals in the ```master_client.py``` and ```client.py``` scripts. 
* Run: First, run the ```master_client.py``` file using the command ```python3 master_client.py <no. of clients>```. Then connect all the clients to the ```master_client.py``` using the command ```python3 client.py <IP of master.py>```. 
* Once all clients are connected, ```master_client.py``` would send the clients to visit the specified ```.onion``` address and download a file. The load balancer would ensure distribution of these clients as per the desired load. 
* ```output.txt``` logs the bandwidth achieved by clients. 
Refer to the [screen recordings](https://purdue0-my.sharepoint.com/:f:/g/personal/arora105_purdue_edu/EhQ2agrf1WlNt-Tjk9-VxWcBxq0rfMPYT5OTr-21dDuCCA?e=9j9cVo) to get help with setup and testing. 

#### Navigation
- **bento**: source for the client and server packages     
- **experiments**: self contained projects/experiments using Bento   
- **testing**: simple tests and sample functions    
- **docs**: [Bento website](https://barc-purdue.github.io/BentoDocs/index.html)


#### Notes:
Tested with python3.6 on Ubuntu 18.04.


#### Starting a Bento server:
Navigate to `bento/server/` and execute:

```
./runserver.py
```

Use `-h` to list the command-line options.  By default, the server listens on
`0.0.0.0:8888` and runs in the current directory.  For storing temporary files,
the server creates the directories `functions/` and `sessions/` if they do
not already exist.


#### Run a sample function as a client:
After starting the Bento server, you can connect to it and test it with the
examples in `testing/`.  For instance, execute:

```
cd testing
./test_hello_world.py   
```

to run a client that uploads and executes a function that simply sends back
"hello world".

Most of the test scripts display a usage statement when passed the `-h`
command-line option.


#### Writing a function:
A Bento function is a normal Python function that runs on a Bento server.
The only difference is that a Bento function executes in an environment that is
initialized with a function API (see `bento/server/core/api.py`) for
communicating with the client.  In particular, the function must use
`api.send()` and `api.recv()` to send and receive data from the client, rather
than `print()` and `input()`.

The Bento client API (see `bento/client/api.py`) provides an RPC interface for
uploading, executing, and performing IO with a function. 

The scripts and functions in `testing/` provide example uses of both the
function and client API.  You can also use `experiments/interactive_client.py`
to send requests to a Bento server from the command-line.


#### Connecting the Bento Client with the Bento Server over Tor:
The Bento client API is unaware of Tor.  To enable the client to communicate
with a Bento server over a Tor circuit, execute the client with the 
[torify](https://gitlab.torproject.org/legacy/trac/-/wikis/doc/TorifyHOWTO)
wrapper.  For instance, to run the `test_hello_world.py` over Tor, enter:

```
cd testing/
torify ./test_hello_world.py
```

`torify` is a utility that comes with Tor; it uses `LD_PRELOAD` to encapsulate
an application's socket calls in the SOCKS protocol and redirect these calls to
a local Onion proxy.  In this way, an application can use Tor without having to
implement native support for Tor.


#### Running functions in an SGX enclave:
By default, a Bento server executes functions using the Python3.6 interpreter
in the standard, userland environment.  To execute functions with the Python
interpreter running in an SGX enclave, instead enter:

```
cd server
./runserver.py -c 'graphene-sgx/pal_loader graphene-sgx/manifest'
```

The `-c` option specifies the command the server uses to execute the function.
In this example, the command specifies to run the Graphene-SGX library
operating system (libOS), and for the libOS to load a Graphene manifest file
for Python.  See [Graphene-SGX](https://github.com/oscarlab/graphene) for
instructions on building the Graphene-SGX library operating system and creating
a manifest file.

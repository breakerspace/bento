### Interactive client
```interactive_client.py``` let's a user send requests to a Bento server on the command line. Write quick functions and easily test them.

#### Usage:  
`python3.6 interactive_client.py`   

#### Example:
```
>> store   
>> enter name: add   
>> enter code (enter three times to submit):   
def add(x, y):   
    sum= x + y   
    return sum   

==recved token: 65ad27c2-5dfd-47bc-8ffd-c4180a2a0818     

>> exec   
>> enter token: 65ad27c2-5dfd-47bc-8ffd-c4180a2a0818   
>> enter call: add(9, 10)   
   
==recvd session_id: 7ee3bc7c-73d8-414b-8057-3c9ebf97aeae   
   
>> open   
>> enter session_id: 7ee3bc7c-73d8-414b-8057-3c9ebf97aeae   

==ok session opened   
   
>> recv   
   
==recved message from session: 7ee3bc7c-73d8-414b-8057-3c9ebf97aeae   
   
19   
```

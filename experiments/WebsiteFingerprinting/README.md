# Website Fingerprinting Experiment

The following instructions detail the setup and procedures for reproducing the website fingerprinting attack against the `Browser` function showcased in our paper.  


## Getting Started

1. Download `Bento-DF.tar`. This archive contains the experiment source code used in the paper.
2. Inside of the download, verify that `pcap-to-df` and `DeepFingerprint-changes` exist. 

3. Verify that `pcap-to-df` contains:
    - `pull-alexa.sh`:  Downloads the Alexa top 1 million sites into a zip'd CSV file.
    - `pcap-to-df-fast.py`: Converts a pcap file of a single visit to an Alexa website on a Tor node running the `Browser` function to the training data for the DeepFingerprinting attack on that site.
    - `make_pickles.py`: Loads the training data in pickle format and creates the test and validation data pickle files.
    - `better-df/pcap-to-df.c`: Creates Tor traffic flow training data by converting the collected traffic flows into their corresponding +/- 1 patterns.

4. Verify that `DeepFingerprint-changes` contains:
    - `ClosedWorld_DF_Bento.py`: Conducts the Deep Fingerprint attack on the Bento `Browser` function.
    - `utility.py`: Provides utility functions to Deep Fingerprinting to load the `Browser` pcap collections.

4. Download the Deep Fingerprinting paper source code from the [repository](https://github.com/deep-fingerprinting/df). Follow the setup instructions and install the necessary dependencies to ensure the provided attack code functions according to the project's provided documentation. Our experiment setup involves 5 NVIDIA 1070 and 2 NVIDIA 1070ti GPUs with the appropriate NVIDIA CUDA graphics drivers on Windows 10. The GPU cluser is connected to a Windows 10 machine named: "ML workstation".

5. To prepare the experiment, create two Amazon EC2 instances and install the Bento server on one and the Bento client on the other. Both instances should have also [Tor](https://www.torproject.org/download/tor/) installed.



## Preparing the Bento client and server

1. On the Bento client, execute `pull-alexa.sh` to download the latest version of the Alexa top 1 million sites and decompress the download.

2. Also on the Bento client, connect to the Bento server and upload the `Browser` function. 

3. Once the `Browser` function has been uploaded, begin recording Tor traffic on the Bento client using `tcpdump`. Ensure that `tcpdump` is saving the Tor traffic associated with the invocation of `Browser(site, padding)` to a pcap file (i.e., `tcpdump -w trial1/site`). 

4. After a single Alexa site has been visited with `Browser`, kill `tcpdump` on the Bento client by issuing: `sudo killall tcpdump`.


## Conduct `Browser` Deep Fingerprinting attack

1. As the Bento client, execute the `Browser` function for each of the top 100 Alexa sites at least 10 times. To follow the demonstrated experiment, conduct the attack using 0 MB, 1 MB and 7 MB of padding, at least 10 times each trial. This equates to each Alexa site being visited with `Browser(site, 0)`, `Browser(site, 1000000)`, and `Browser(site, 7000000)`.  For each trial of the experiment, create a new folder with the 100 collected pcap files. 

2. Download the collected pcap trail folders to "ML workstation".

3. On "ML workstation", execute: `python pcap-to-df-fast.py trialX` where `X` is the trial number corresponding to the generated trials folder. This script will create `X_train.pkl` and `Y_train.pkl` training data files.

4. Execute `python make_pickles.py` to create the test and validation data. This script also normalizes the test data as shown in the experiment setup in the Deep Fingerprinting paper.

5. Lastly, for each of the three padding sizes, run the modified Deep Fingerprinting attack code in: `DeepFingerprint-changes` using the collected datasets. The provided deep fingerprinting attack code differs to that of the original authors' because code to load the `Browser` dataset into the ML model (see: `LoadDataBentoCW()` in `utility.py`) is included. Much like the original Deep Fingerprinting attack, the provided code will train the model with 30 epochs. The output of the evaluation will contain the final attack accuracy on website fingerprinting using the `Browser` function.


## Conduct Deep Fingerprinting attack on Unmodifed Tor

1. On "ML workstation", run the Deep Fingerprinting attack using the authors' provided "NoDef" dataset. By default, the attack model will be trained with 30 epochs. The output of the evaluation will contain the final attack accuracy on non-defended Tor.




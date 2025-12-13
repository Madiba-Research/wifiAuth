# to collect data
We orignially select 5 locations to collect AP info:
seat
door
corner
cross
elevator
Now check the google doc about location info

# to access data from mobile phone
Use adb to tar the files
```sh
su
tar cvf /sdcard/wififiles.tar -C /data/data/com.example.wifirttmeasure/files .
```
then adb pull to the computer
or:
```sh
find . -name '*t0.json' | xargs tar cvf /sdcard/wififilest0.tar
```



# to train
Run **ProcessRawData.py**, with correct folder name
it generates a new folder make data into graph input

> in current setting:
> we set the output with as a vector with 8 dimension, as it meets our current dataset
> Thereafter, we set the lattice with dimension of 8

with valid graph data input, run **trainfuzzy.py** to train the model, **predictFuzzy.py** to predict graph

# to prepare lattice encoding
set the parameter, i.e., dimension, element, ... of **generateMatrix.py** and run, to obtain the G and H in npz file


# easy way to let phone access API
adb reverse --list
adb reverse tcp:5000 tcp:5000

# another easy way to let phone access API
install tailscale on both ip-unexposed server and phone. And make the phone can find the server.
After that, make sure that phone's wifi is on and no connection with any wifi, which provide better connection for tailscale.


# about dataset
**wifiData1** and **wifiData2** contain training data, each one contains data of three positions.
Both dirs' data collected from same position, but in two different time session.

**data630** is data from **wifiData1** and **wifiData2**, only containing p1
**data630d1** is data from **wifiData1** and **wifiData2**, containing both p1 and p2
**data630d2** is data from **wifiData1** and **wifiData2**, containing both p2 and p3
**data630d3** is data from **wifiData1** and **wifiData2**, containing both p1 and p3

**wifiOneLoc** is the data collected sorely from one location. It is used to explore the range of the location.

# Sep 19 plan
Given figure 5, we check:
1. if we discard those samples away from 1 s-dev, and then 2 s-dev.
2. then the registration range shrinks.
3. see how the new range performs on the verification data.

## To Registrate & Authenticate in Batch with existing data
Use **utils/registrationCall.py** and **utils/authenticateCall.py**


# Sep 28
Now we have d5 registration and authentication, but we didn't have d5 model trained. d3 model is still using in this scenario.


# Oct 15
New data preprocessed with **processRawData2**, which could generate graph with an additional category file, for later triplet generation with hard negative mining data.

we use **trainfuzzy3** on model **Encoderfuzzy3**. to get 32 dim output vector, with trained model **best_630d3norm_hnm_model3**

Then we use **processRawData4**, which generate graph with bssid feature but no more explicit bssid usage.

# We investigate the relationship between H and triplet loss margin
unit length of integer space is mapping to lattice space with:
```
max length of v_x: 2.9510272812705285
min length of v_x: 1.2517879539233665
```
Therefore we consider margin as 1.3, or 2.6, in between 1.25 and 2.95

We set the model with max pool, instead of mean pool.

# Oct 18
With max pool, we tried margin with 1.25 (cannot train) -> 1.3 (ok) -> 1.5 (still ok but better than 1.3) -> 3.0 (bad)
todo: match margin with 2.95, because of max pool -> done but some failed

recall with global_mean_pool, our best performance is margin 4 (0.98 tar and 0.1 far at 7m)

mix pool:

we use **trainfuzzy31** on model **Encoderfuzzy31**, for mix pool:
0.98 / 0.48 for 7m

Then we did other version, with residual

Latest idea:

only with rssi fingerprint.

# Rssi Fingerprint performance on Simple MLP
7m: tar-1.0, far-0.78 (margin 3)

This time we add dataset shuffle in training

Simple CNN with margin 3: tar-0.82, far-0.16

back to gnn-maxpool with margin 3.0:
3m:
Overall True acceptance rate (TAR): 74.00%
Overall False acceptance rate (FAR): 30.00%

5m:
Overall True acceptance rate (TAR): 70.00%
Overall False acceptance rate (FAR): 2.00%

7m:
Overall True acceptance rate (TAR): 80.00%
Overall False acceptance rate (FAR): 0.00%


back to gnn-meanpool with margin 4.0:
(still trainfuzzy3 and encoderfuzzy3, but change maxpool to meanpool)

# current best version:
7m: tar-0.98, tar-0.02 (margin 4)

with model: best_630d3norm_hnm_meanpool_a4_random.pth

auth_system = AuthSystem("H_G_demo_32_dimension.npz", "usersd3normDict_main_pool_randomtrain.db")

# Comparison
Then we use same model, but NFE method (we implemented "authAppNFE.py")

authsense:
Authentication success rate for d3p3: 1.0000
Authentication success rate for d3p1: 1.0000
Authentication success rate for d3p3 (from d3p1): 0.6400
Authentication success rate for d3p1 (from d3p3): 0.5200
Overall TAR: 1.0000, Overall FAR: 0.5800
Authentication success rate for d3p1: 1.0000
Authentication success rate for d3p1: 1.0000
Authentication success rate for d3p5 (from d3p1): 0.2800
Authentication success rate for d3p1 (from d3p5): 0.0800
Overall TAR: 1.0000, Overall FAR: 0.1800
Authentication success rate for d3p7: 0.8400
Authentication success rate for d3p1: 1.0000
Authentication success rate for d3p7 (from d3p1): 0.0400
Authentication success rate for d3p1 (from d3p7): 0.0000
Overall TAR: 0.9200, Overall FAR: 0.0200

# ROC plot
dev = 1: log_auth_nov6_sigma10
3m: tar=0.66, far=0.22
5m: tar=0.78, far=0.04
7m: tar=0.78, far=0.0

dev = 1.5: log_auth_nov6_sigma15
3m: tar=0.82, far=0.3
5m: tar=0.94, far=0.14
7m: tar=0.94, far=0.0

dev = 2: log_auth_gnnmeanpool_randomtrain
3m: tar=0.96, far=0.82
5m: tar=0.98, far=0.28
7m: tar=0.98, far=0.02

dev = 2.5:  log_auth_nov6_sigma25
3m: tar=1.0, far=0.86
5m: tar=1.0, far=0.36
7m: tar=1.0, far=0.12

dev = 3: log_auth_nov6_sigma30
3m: tar=1.0, far=0.9
5m: tar=1.0, far=0.5
7m: tar=1.0, far=0.22



# findEER
this file, should test our own eer, with graunlar scale, and generate data like authentisense Figure 5.a:

use **noSfAuthApp.py** and reg/auth for **sfRegistrationCall.py** and **sfAuthenticateCall25user.py**,

then **SfDistanceStat25.py** to get result.

bad user: t6, t7, t11, t12, t21, we remove them

a bit influence: t10, t15, t20, t24

evaluation eer user | test user:

1 2 3 4 5   8 9 10  13 15 | 14 16 17 18 19 20  22 23 24

# for anonamity
User name is replaced with **noname**

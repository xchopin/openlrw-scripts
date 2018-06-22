# OpenLRW scripts

OpenLRW-scripts is a repository where you can find scripts to populate the Apero OpenLRW API by using different sources. These scripts are used at the [University of Lorraine](https://en.wikipedia.org/wiki/University_of_Lorraine) and are open-source.

## I. Requirements
 - [OpenLRW](https://github.com/Apereo-Learning-Analytics-Initiative/OpenLRW)
 - [Logstash](https://www.elastic.co/fr/downloads/logstash) (≥ 2.4)
 - [Python](https://www.python.org/downloads/)
    - [python-ldap](#2-python-ldap)
    - [PyYAML](#3-pyyaml)
    - [MySQLdb](#4-MySQLdb)
    - [OpenLDAP](https://stackoverflow.com/a/4768467/7644126)

## II. Sources used to import data
- LDAP
- Log files from [CAS applications](https://en.wikipedia.org/wiki/Central_Authentication_Service)
- [Moodle LMS](https://moodle.com/)
- CSV from Apogée [(a software for the French universities)](https://fr.wikipedia.org/wiki/Apog%C3%A9e_(logiciel))


## III. Get started
### A. Clone the repository
`$ git clone https://github.com/xchopin/OpenLRW-scripts.git`

### B. Create and edit the settings file
```bash 
$ cd OpenLRW-scripts/bootstrap
$ cp settings.yml.dist settings.yml ; vi settings.yml
```

### C. Install the Python libraries
> To get the libraries you will need to have [PIP package manager](https://pypi.python.org/pypi/pip)

- #### 1. Download and install PIP
   `$ wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py ; python /tmp/get-pip.py`

- #### 2. python-ldap
   `$ pip install python-ldap` 
   
- #### 3. PyYAML
   `$ pip install pyyaml` 
   
- #### 4. MySQLdb   
   `$ pip install mysqlclient`
 

## IV. Usage
### A. Users (mongoUser collection)
 > This script will import the users by using the LDAP database and the CSV files; there are 2 arguments possible

- #### 1. Populate the collection
    > Clears then populates the collection (faster)

    `$ python collection/Users/import_users.py reset`    


- #### 2. Update the collection
    > Adds the new users to the collection (slower: checks duplicates)

    `$ python collection/Users/import_users.py update`  

### B. Caliper Events (mongoEvent collection)
#### 1. Add CAS authentications to the collection
 > This script will import the "logged-in" events (students only)  by using log files
 
- ##### For one log file
```bash
$ cd collections/Events/CAS/
$ cat /logs/cas_auth.log | /opt/logstash/bin/logstash --quiet -w10 -f authentication.conf
```  

- ##### Treating a plenty of log files (from a date to YESTERDAY)
```bash
$ cd collections/Events/CAS/
$ sh authentications.sh
```  

#### 2. Add Moodle events to the collection

 > Import events from a timestamp

 `$ python collection/Events/Moodle/import_events.py TIMESTAMP` 
 
 > Import events from a timestamp to another timestamp
 
  `$ python collection/Events/Moodle/import_events.py TIMESTAMP TIMESTAMP` 

## V. License
OpenLRW-scripts is made available under the terms of the [Educational Community License, Version 2.0 (ECL-2.0)](https://opensource.org/licenses/ECL-2.0).

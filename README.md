# stackato-ad-import
Import organisations from Active Directory groups and then import member users into Stackato as "users" in those Orgs

## Installation
```
pip install -r requirements
```

Currently the script also relies on the stackato client being on the path. This has only been tested on MacOS and *NIX currently, Windows would probably need the path modifying. 

I have found it simplest to run this from the root of the Stackato controller VM itself. In order to install the requirements however I executed the following...
```
sudo apt-get install python-ldap
```
## Usage

Modify the variables at the top of the script to match your environment.

(TODO: Pull this out to a YAML config file)
```
ldapstring = "ldap://10.12.0.11"                                  # String to define the host and protocol to connect to AD via LDAP
adusername = "CN=stackadmin,ou=HPE,dc=adtest,dc=hpcloud,dc=net"   # The DN for the user used to bind to AD. Requires Read access
adpassword = "Hpinvent01"                                         # Password for the bind user
basedn = "ou=HPE,dc=adtest,dc=hpcloud,dc=net"                     # DN for the OU from which to import the groups as orgs
userbasedn = "dc=adtest,dc=hpcloud,dc=net"                        # DN to start searching for the users (can be different from basedn)
groupfilter = "Org*"                                              # Filter on the groupname to select which groups to import
ldfilter = "(&(cn=" + groupfilter + ")(objectCategory=group))"    # Full group filter string
stacktarget = "api.stackato.adtest.hpcloud.net"                   # Stackato Endpoint address
stackuser = "stackato"                                            # Stackato admin user
stackpassword = "Hpinvent01"                                      # Stackato admin address
stackdefaultpassword = "Hpinvent01"                               # The default password to give to all imported users
defaultspace = "default"                                          # The name of the space to create in all new orgs
```
Execute the script with the following... (It requires Python 2.7)
```
python stack-ad-import.py
```
The script will automatically gather all users and import the organisation and users without any further prompts! Ensure this is what you intened to do and that your BASE DN and filters are correct! The script currently does not include nested users, so if a user is only a member of a group that is a member of the target group, they will not be included.

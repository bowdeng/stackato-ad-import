import ldap
import subprocess
import json

ldapstring = "ldap://10.12.0.11"
adusername = "CN=stackadmin,ou=HPE,dc=adtest,dc=hpcloud,dc=net"
adpassword = "Hpinvent01"
basedn = "ou=HPE,dc=adtest,dc=hpcloud,dc=net"
userbasedn = "dc=adtest,dc=hpcloud,dc=net"
groupfilter = "Org*"
ldfilter = "(&(cn=" + groupfilter + ")(objectCategory=group))"
stacktarget = "api.stackato.adtest.hpcloud.net"
stackuser = "stackato"
stackpassword = "Hpinvent01"
stackdefaultpassword = "Hpinvent01"
defaultspace = "default"

l = ldap.initialize(ldapstring)

try:
    l.protocol_version = 3
    l.simple_bind_s(adusername, adpassword)
    valid = True
    print "Successfully Bound"
except Exception, error:
    print error
    exit(1)

#    filter = "(|(uid=" + user + "\*)(mail=" + user + "\*))"
results = l.search_s(basedn, ldap.SCOPE_SUBTREE, ldfilter)

neworgs = {}
newusers = {}

# Build list of Orgs and Users from AD
for dn, entry in results:
    dn = str(dn)
    org = dn.split(',', 1)[0].split('=', 1)[1]
    if not neworgs.has_key(org):
        print org
        neworgs[org] = {}
        userfilter = "(&(objectClass=user)(memberof=" + dn + "))"
        userresults = l.search_s(userbasedn, ldap.SCOPE_SUBTREE, userfilter)
        for udn, uentry in userresults:
            username = uentry['sAMAccountName'][0]
            if uentry.has_key("mail"):
                email = uentry['mail'][0]
            else:
                email = uentry['userPrincipalName'][0]
            neworgs[org][username] = email
            if not newusers.has_key(username):
                newusers[username] = email
            print "   " + username + " (" + email + ")"


# Login to Stackato
res = subprocess.Popen(["stackato", "target", stacktarget], stdout=subprocess.PIPE).communicate()[0]
res = subprocess.Popen(["stackato", "login", stackuser, "--credentials", "password:" + stackpassword],
                       stdout=subprocess.PIPE).communicate()[0]

# Get a list of orgs from Stacakto
orgslist = json.loads(subprocess.Popen(["stackato", "orgs", "--json"], stdout=subprocess.PIPE).communicate()[0])

# Get a list of existing users from Stackato
userslist = json.loads(subprocess.Popen(["stackato", "users", "--json"], stdout=subprocess.PIPE).communicate()[0])

# Create a list of exsiting usernames
susers = []
for suser in userslist:
    uname = suser['entity']['username']
    if uname not in susers:
        susers.append(uname)

# Add any new users
for uname, email in newusers.iteritems():
    if uname not in susers:
        print "Creating user " + uname
        res = subprocess.Popen(["stackato", "create-user", uname, "--email", email, "--password", stackdefaultpassword],
                               stdout=subprocess.PIPE).communicate()[0]

# Create a dict of existing orgs
sorgs = {}
for sorg in orgslist:
        sorgname = sorg['entity']['name']
        if not sorgs.has_key(sorgname):
            sorgs[sorgname] = []
            orguserlist = json.loads(subprocess.Popen(["stackato", "org-users", sorgname, "--json"],
                                                      stdout=subprocess.PIPE).communicate()[0])
            for user in orguserlist['user']:
                if user not in sorgs[sorgname]:
                    sorgs[sorgname].append(user)

for orgname, org in neworgs.iteritems():
    if not sorgs.has_key(orgname):
        print "Creating Org " + orgname
        res = subprocess.Popen(["stackato", "create-org", orgname], stdout=subprocess.PIPE).communicate()[0]
        print "Creating 'default' space for " + orgname
        res = subprocess.Popen(["stackato", "create-space", defaultspace], stdout=subprocess.PIPE).communicate()[0]
        sorgs[orgname] = []
        print orgname + " creation complete."

    for u in org:
        if u not in sorgs[orgname]:
            sorgs[orgname] = u
            print "Adding user " + u + " to Org " + orgname
            res = subprocess.Popen(["stackato", "link-user-org", u, orgname], stdout=subprocess.PIPE).communicate()[0]
            print "Adding user " + u + " to space " + orgname + "/default"
            res = subprocess.Popen(["stackato", "link-user-space", u, defaultspace, "--organization", orgname],
                                   stdout=subprocess.PIPE).communicate()[0]

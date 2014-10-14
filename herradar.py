from mechanize import Browser
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from time import sleep
from datetime import date
from datetime import datetime
from collections import deque
import lxml
import cPickle as pickle
import random
import smtplib
import sys
import traceback

# TODO : improve checking for profile changes, make more efficient?
# TODO : change cycle interval to reflect actual time difference starting from end of data extraction from okc

#################################################################################
# ACCOUNT INFORMATION                                                           #
#################################################################################

# This is the email account you wish to receive these alerts on
receivingEmailAddress = ""

# You need to supply a gmail account in order to send the alerts
# create one and fill in the username and password (ignore the gmailAddress variable)
gmailUsername = ""
gmailPassword = ""
gmailAddress = gmailUsername + "@gmail.com"

# TODO 2: create new okc login since this will be visiting profiles, disable visiting on new login
# Supply an OkCupid account.  If you aren't a premium user and have invisible mode enabled you may want to make a throwaway
okCupidUsername = ""
okCupidPassword = ""

#################################################################################
# SEARCH PARAMETERS                                                             #
#################################################################################

# TODO 2: get searchURL
# Do a search on OKC, using all of the preferences, filters, and options you want this script to use
# then paste the URL in this value 
searchURL = ""

# Terms to search tracked profiles for, case insensitive
searchTerms = ['rockin', 'hammer', 'love', 'gifts', 'slime', 'gaming', 'boxing']

#################################################################################
# OTHER BOT SETTINGS                                                            #
#################################################################################

# Specify where entity information is saved on your machine
# You can specify a different path or just use the file name to store in the same directory
# If the script has issues reloading collections after starting, change these to the absolute path where you run the script
taggedSaveLocation = "./taggedEntities.pk"
trackingSaveLocation = "./trackingEntities.pk"

# Length of time between cycles in seconds
sleepInterval = 3*60

# Percentage of random variation between cycles (to make this look less like a bot
sleepVariation = .1

# length of time for tracking in days, after the Nth day, tracking stops
trackingAge = 7

#################################################################################
# DO NOT MODIFY ANYTHING BELOW THIS                                             #
#################################################################################

tagged = []
tracking = {}

# Set up Error reporting
def my_excepthook(type, value, tb):
    #sendEmail('herRadar has crashed', 'incoming crash report')
    traceBack = traceback.format_exception(type, value, tb)
    errorMsg = ''
    try :
        errorEntity = entity
    except NameError :
        errorEntity = "NA"
    for line in traceBack :
        errorMsg = errorMsg + line + '<br>'
    msg = """herRadar has crashed <br> here is a traceback of the exception <p>""" + errorMsg + """<p>The current entity was: <br>""" + errorEntity
    sendEmail('herRadar has crashed', msg)
    sys.__excepthook__(type, value, tb)

sys.excepthook = my_excepthook

def loadCollections() :
    global tagged
    global tracking
    try :
        with open(taggedSaveLocation, 'rb') as input :
            tagged = pickle.load(input)
    except IOError :
        print taggedSaveLocation
        print "Previously tagged entities not found, creating new collection"
        tagged = []

    try :
        with open(trackingSaveLocation, 'rb') as input :
            tracking = pickle.load(input)
    except IOError :
        print "Currently tracked entities not found, creating new collection"
        tracking = {}

def saveCollections() :
    try :
        with open(taggedSaveLocation, 'wb') as output :
            pickle.dump(tagged, output, pickle.HIGHEST_PROTOCOL)
    except IOError :
        print "Error while saving"
        
    try :
        with open(trackingSaveLocation, 'wb') as output :
            pickle.dump(tracking, output, pickle.HIGHEST_PROTOCOL)
    except IOError :
        print "Error while saving"
  
def sendEmail(subject, msg) :
    mime = MIMEMultipart('alternative')
    mime['Subject'] = subject
    mime['From'] = gmailUsername
    mime['To'] = receivingEmailAddress
    mime.attach(MIMEText(msg, 'html'))
      
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()  
    server.login(gmailUsername, gmailPassword)  
    server.sendmail(gmailAddress, receivingEmailAddress, mime.as_string())  
    server.quit()
    
    #print 'Sending Email: \n' + subject + '\n' + msg
    print 'Sending email'

class acNode :
    def __init__(self, ch) :
        self.char = ch
        self.transitions = []
        self.results = []
        self.fail = None

class searchTree :

    def __init__(self) :
        self.terms = []
        self.root = None

    def add(self, term) :
        self.terms.append(term)

    def make(self) :
        # Create the root node and queue for failure paths
        root = acNode(None)
        root.fail = root
        queue = deque([root])

        # Create the initial tree
        for keyword in self.terms :
            current_node = root
            for ch in keyword :
                new_node = None
                for transition in current_node.transitions:
                    if transition.char == ch:
                        new_node = transition
                        break

                if new_node is None:
                    new_node = acNode(ch)
                    current_node.transitions.append(new_node)
                    if current_node is root:
                        new_node.fail = root

                current_node = new_node
            current_node.results.append(keyword)

        # Create failure paths
        while queue:
            current_node = queue.popleft()
            for node in current_node.transitions:
                queue.append(node)
                fail_state_node = current_node.fail
                while not any(x for x in fail_state_node.transitions if node.char == x.char) and fail_state_node is not root:
                    fail_state_node = fail_state_node.fail
                node.fail = next((x for x in fail_state_node.transitions if node.char == x.char and x is not node), root)

        # tree has been built! return it
        self.root = root

    def search(self, text) :
        hits = []
        currentNode = self.root

        # Loop through characters
        for c in text :
            # Find next state (if no transition exists, fail function is used)
            # walks through tree until transition is found or root is reached
            trans = None
            while trans == None :
                # trans=currentNode.GetTransition(text[index])
                for x in currentNode.transitions :
                    if x.char == c :
                        trans = x
                if currentNode == self.root : break
                if trans==None : currentNode=currentNode.fail
                
            if trans != None : currentNode=trans
            # Add results from node to output array and move to next character
            for result in currentNode.results :
                hits.append(result)
  
        # Convert results to array
        return hits
            
# Load list of tagged entities
loadCollections()
print 'Loaded collections'

print 'Creating search tree'

tree = searchTree()
for term in searchTerms :
    tree.add(term.lower())
tree.make()

# Send notification to the gmail account that the server is running
sendEmail("HerRadar is now activated", "")

while 1 == 1 :
  
    # Create boolean to determine if a save is necessary
    saveNeeded = False
    
    print 'Opening browser'
    
    # Create the browser and begin accessing sites
    browser = Browser()

    # Log in to OkCupid
    browser.open("http://www.okcupid.com/login")
    
    # New fix to select the correct form
    formcount=0
    for f in browser.forms():  
        if str(f.attrs["id"])=="loginbox_form":
            break
        formcount=formcount+1
        
    browser.select_form(nr=formcount)
    browser['username']=okCupidUsername
    browser['password']=okCupidPassword
    browser.submit()
    
    # Access search page for OKC
    response = browser.open(searchURL)
    content = response.read()
    
    # Pull user html tags from OKCupid data
    soup = BeautifulSoup(content, "lxml")
    #soup = BeautifulSoup(content)
    nameTags = soup.find_all(attrs={"class": "name"})
    
    print 'Extracting entity list'
    
    # Strip the usernames from the tags
    collection = []
    for entity in nameTags :
        collection.append(entity.string.encode('ascii', 'ignore'))

    # Print list of entities seen
    print 'Entities found ', collection

    # Get Current Date
    today = date.today()
 
    # Look for new entities
    print 'Looking for new entities'    
    
    for entity in collection :
    
        if (tagged.count(entity) == 0) :
            tagged.append(entity)
            
            if (not entity in tracking) :
            
                # Add entity info to the tracking list
                try :
                    entityAge = soup.find(id='usr-'+entity).find(attrs={"class": "age"}).string.encode('ascii', 'ignore')
                except KeyError :
                    entityAge = 'ERROR'
                    print "There was a keyError generating entityAge for " + entity
                
                try :
                    entityImage = soup.find(id='usr-'+entity).a['data-image-url'].encode('ascii', 'ignore')
                except KeyError :
                    entityImage = 'ERROR'
                    print "There was a keyError generating entityImage for " + entity
                
                entityProfile = 'http://okcupid.com/profile/' + entity
                
                # Save entity info to tracking list
                print 'Entity: ' + entity + ', added to tracking'
                tracking[entity] = [today, "", entityAge, entityImage, entityProfile]

            # Update boolean so lists are saved after this cycle
            saveNeeded = True

    # TODO 2 : do I want to check tracked entities now? or more / less frequently?
    
    # Remove old entries
    print 'Removing expired entities from tracking'
    expired = []
    for entity in tracking :
        entityDate = tracking[entity][0]
        # Remove entities from tracking if over age
        if (today - entityDate).days > trackingAge :
            expired.append(entity)
            
    for entity in expired :
        print 'Removing Entity: ' + entity
        del tracking[entity]
        
    # If any entities are expired, update boolean so lists are saved after this cycle
    if len(expired) > 0 :
        saveNeeded = True
    
    # Check tracked entities
    print 'Checking tracked entities for changes'
    for entity in tracking :

        tuple = tracking[entity]
    
        # Remove entities from tracking if over age
        if (today - tuple[0]).days > trackingAge :
            print 'Entity: ' + entity + ', removed from tracking'
            
            del tracking[entity]
            
            # Update boolean so lists are saved after this cycle
            saveNeeded = True
            
        # Check pre-existing entities for changes to profile
        else :
            response = browser.open('http://okcupid.com/profile/' + entity)
            content = response.read()
            soup = BeautifulSoup(content)
            
            # Iterate through each profile section and pull out text; try/catch block for sections that don't exist
            profile = ''
            for i in range(10) :
                essayID = 'essay_text_' + str(i)
                essayContent = soup.find(id=essayID)
                try :
                    profile += essayContent.text.encode('ascii', 'ignore')
                except AttributeError :
                    profile += ''

            # Check for changes to the profile
            if profile != tuple[1] :

                print 'Entity: ' + entity + ', has changes to profile'

                # Search for keywords
                results = []
                resultString = ''
                for result in tree.search(profile.lower()) :
                    results.append(result)
                    resultString += result + ', '
                    '''
                    if acSearch :
                        results.append(profile[result[0], result[1]])
                        resultString += profile[result[0], result[1]] + ', '
                    else :
                        results.append(result)
                        resultString += result + ', '
                    '''
                
                # Check for matches
                if len(results) > 0 :
                    # Debug
                    print 'Entity: ' + entity + ' has matched terms: ', results
                    
                    # Report a match!
                    msg = """The following terms were found: <br>
                    """ + resultString + """ <br>
                    For User: """ + entity + """ <br>
                    Age: """ + tuple[2] + """ <br>
                    <img src='""" + tuple[3] + """'><br>
                    <a href='""" + tuple[4] + """'>Profile</a>
                    <br> <br>
                    This message means that either the entity just added these terms to their profile or has just updated it.
                    """
                    
                    sendEmail('Tracking result for ' + entity, msg)
                    
                # Update stored profile
                tuple[1] = profile
                
                # Update boolean so lists are saved after this cycle
                saveNeeded = True

    browser.close()
    
    # Save the tagged list of entities
    if (saveNeeded) :
        print "Saving collections"
        saveCollections()
        print "Collections saved"
    
    # see if it's time to send a heartbeat
    time = datetime.now().time()
    if time.hour == 12 & time.minute < 10 :
        sendEmail('herRadar is active', 'thump')
    
    # Wait and repeat
    sleep(random.randint(int(sleepInterval-(sleepVariation*sleepInterval)), int(sleepInterval+(sleepVariation*sleepInterval))))

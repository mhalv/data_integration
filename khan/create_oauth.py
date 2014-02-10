import oauth2 as oauth
import time
import httplib2 
from urlparse import urlparse, parse_qs
import ast
import os

# Set the API endpoints (request and access token), as well the consumer key and consumer secret 
REQUEST_TOKEN_URL = "http://www.khanacademy.org/api/auth/request_token"
ACCESS_TOKEN_URL = 'http://www.khanacademy.org/api/auth/access_token'
KHAN_USER_URL = "http://www.khanacademy.org/api/v1/user"
CONSUMER_KEY = open("C:/data_robot/logistical/khan_consumer_key.txt", "r").read()
CONSUMER_SECRET = open("C:/data_robot/logistical/khan_consumer_secret.txt", "r").read()

# Helper method to clean literal response strings to proper Python sytnax
def cleanup_khan_response(string):
    return string.replace("false","False").replace("true","True").replace("null","'null'")


# Helper Method to create 'slugs' and make directory names cleaner
def slugify_user(string):
    # Remove @ for _ and . for _
    slug_string = string.replace("@","_").replace(".","_")
    # Some users have http://nouserid.khanacademy.org/7e1
    # Remove http://, replace / with _
    slug_string = slug_string.replace("http://","").replace("/","_")
    # Return slugified string
    return slug_string

def generate_request_token(): 
    # Set the base parameters required by the API call.
    params = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'oauth_signature_method':'HMAC-SHA1',
        'oauth_consumer_key':CONSUMER_KEY,
        'oauth_consumer_secret':CONSUMER_SECRET,      
        }
    
    # Setup the Consumer with the api_keys given by the provider
    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
    
    # Create our request. Change method accordingly.
    req = oauth.Request(method="GET", url=REQUEST_TOKEN_URL, parameters=params)

    # Create the signature
    signature = oauth.SignatureMethod_HMAC_SHA1().sign(req,consumer,None)

    # Add the Signature to the request
    req['oauth_signature'] = signature

    # Make the request to get the oauth_token and the oauth_token_secret
    # I had to directly use the httplib2 here, instead of the oauth library.
    h = httplib2.Http()
    resp, content = h.request(req.to_url(), "GET")
    print "Ok, we sent a request token. Now you need to authorize it with either: A Google, Facebook or Khan account" 
    print "Go to the following link in your browser to authorize: %s" % (str(resp['content-location']))
    print "(NOTE: This link will be valid until %s)" % (str(resp['expires']))  
    print "\nPress 'Enter' once you authorize and see 'OK' in the browser (ALSO DON'T CLOSE THE BROWSER WINDOW!)"
    dumy_enter = raw_input()
    print "Paste the browser URL here (where you're seeing 'OK'). NOTE: The url should contain the parameters oauth_token_secret and oauth_token"
    print "(e.g. http://www.khanacademy.org/api/auth/default_callback?oauth_token_secret=BLASECRETBLASECRET&oauth_token=BLABLABLABLA)"
    url_with_tokens = raw_input()
    # Now parse out the oauth_token_secret and oauth_token
    oauth_token_secret = ""
    oauth_token = ""
    try:
        o = urlparse(url_with_tokens)
        params = parse_qs(str(o.query))
        if 'oauth_token_secret' not in params or 'oauth_token' not in params:
            # There's no oauth_token_secret or oauth_token in the URL, throw error 
            raise Exception
        else:
            oauth_token_secret = params['oauth_token_secret'][0]
            oauth_token = params['oauth_token'][0]
    except Exception,e:
        # Catch error if the URL is malformed
        print str(e)
        print "Oops that url you pasted doesn't look right, we couldn't get the oauth_token_secret and oauth_token values out of it, try again!" 
        exit(0)
    return oauth_token, oauth_token_secret


def generate_final_token(oauth_token,oauth_token_secret): 
    # Setup the Consumer with the api_keys given by the provider
    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)

    # Setup the token 
    token = oauth.Token(key=oauth_token, secret=oauth_token_secret)
    
    # Set up params to get final token 
    params_for_final_token = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'oauth_signature_method':'HMAC-SHA1',
        'oauth_CONSUMER_KEY':CONSUMER_KEY,
        'oauth_token': token
        }

    oauth_request = oauth.Request.from_consumer_and_token(
        consumer=consumer,
        token=token,
        http_url = ACCESS_TOKEN_URL,
        parameters = params_for_final_token,
        http_method='GET'
        )

    # Create the signature
    oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)

    # Make the request to get the final tokens
    # I had to directly use the httplib2 here, instead of the oauth library.
    h = httplib2.Http()
    resp, content = h.request(oauth_request.to_url(), "GET")
    final_oauth_token_secret = ''
    final_oauth_token = ''
    try:
        final_tokens = parse_qs(str(content))
        if 'oauth_token_secret' not in final_tokens or 'oauth_token' not in final_tokens:
            # There's no oauth_token_secret or oauth_token in the URL, throw error 
            raise Exception
        else:
            final_oauth_token_secret = final_tokens['oauth_token_secret'][0]
            final_oauth_token = final_tokens['oauth_token'][0]
    except Exception,e:
        # Catch error if the URL is malformed
        print str(e)
        print "Oops that response we got from Khan didn't look right, we couldn't get the oauth_token_secret and oauth_token values out of it, try again!" 
        exit(0)
    return final_oauth_token,final_oauth_token_secret


# Method to test initial API request and get user/coach email 
def make_api_request(oauth_token,oauth_token_secret):
    # Setup the Consumer with the api_keys given by the provider
    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)

    # Setup the token 
    token = oauth.Token(key=oauth_token, secret=oauth_token_secret)

    params = {
        'oauth_version': "1.0",
        'oauth_nonce': oauth.generate_nonce(),
        'oauth_timestamp': int(time.time()),
        'oauth_signature_method':'HMAC-SHA1',
        'oauth_consumer_key':CONSUMER_KEY,
        'oauth_token': token
        }
    
    oauth_request = oauth.Request.from_consumer_and_token(
        consumer=consumer,
        token=token,
        http_url = KHAN_USER_URL,
        parameters = params,
        http_method='GET'
        )
    
    oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)
    
    # Make the request to get the oauth_token and the oauth_token_secret
    # I had to directly use the httplib2 here, instead of the oauth library.
    h = httplib2.Http()
    resp, content = h.request(oauth_request.to_url(), "GET")
    try: 
        print "Testing to see if we can connect to Khan"
        if resp['status'] == '200':
            print "Great! Got back a good response (HTTP status 200)"
            parsed_dictionary_test = ast.literal_eval(cleanup_khan_response(content))
            # WARNING: 'key_email' sometimes returns a different user than the actual authenticated email 
            # reported by Andrew on March-1-2013 
            # Use
            #target_coach = parsed_dictionary_test['key_email']
            target_coach = ""
            for auth_email in parsed_dictionary_test['auth_emails']:
                if auth_email.startswith("norm:"):
                    # Use the norm: email inside auth_emails
                    target_coach = auth_email.replace("norm:","")
                    break 
            return target_coach
        else: 
            print "Not good, got back bad response"
            print "The HTTP response status was " + str(resp['status'])
            print "TIP: Try running create_oauth.py if it was an invalid token. The token could have expired or been revoked unknowingly"
            print "%s" % (content)        
    except Exception,e: 
        print "Oops, something went wrong getting the response from the initial test, the error was " + str(e)


def main():
    ## Start the sequence 
    ## First send a request toekn 
    oauth_token, oauth_token_secret = generate_request_token()
    print "Great! We now have the oauth_token and oauth_token_secret" 
    print "These are throw away values anyways needed for the final token, but they're oauth_token:'" + str(oauth_token) + "' and oauth_token_secret:'" + str(oauth_token_secret) + "'"
    ## Got back initial auth token and secret, need to resend to get final token and secret token 
    print "Making a third and final call to Khan to get the FINAL token"
    final_oauth_token, final_oauth_token_secret = generate_final_token(oauth_token,oauth_token_secret)
    print "Great! We now have the FINAL oauth_token and oauth_token_secret to make API calls" 
    print "The FINAL tokens are oauth_token:'" + str(final_oauth_token) + "' and oauth_token_secret:'" + str(final_oauth_token_secret) + "'"
    # Create a file and place these FINAL tokens to make API calls down the line 
    print "Making an API call to confirm the FINAL oauth token is working"
    coach = make_api_request(final_oauth_token, final_oauth_token_secret)
    print "Ok, the FINAL oauth token belongs to %s" % (coach)
    target_dir = "%s" % (slugify_user(coach))
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    print "Will now save tokens to %s/tokens.py" % (slugify_user(coach))
    file = open('%s/tokens.py' %(slugify_user(coach)), 'w+')
    file.write('FINAL_OAUTH_TOKEN="%s"\n' % (final_oauth_token)) 
    file.write('FINAL_OAUTH_TOKEN_SECRET="%s"\n' %(final_oauth_token_secret))
    file.close()
    # Also very important create an __init__.py file to allow import 
    file2 = open('%s/__init__.py' %(slugify_user(coach)), 'w+')
    file2.close()

if  __name__ =='__main__':
    main()

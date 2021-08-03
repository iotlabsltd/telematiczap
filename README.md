# The TelematicZap project
## Auto transform telematics data from one format to another.
This is an open-source django project funded by DAPSI, and developed by Konetik.  
To setup the project, along with a superuser, type:  
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

To start the project, simply type:  
```
python manage.py runserver
```


## Feature: administration panel  
`http://localhost:8000/admin`


## Feature: register client applications to use data on TelematicZap
TelematicZap provides the interface of an OAuth 2 Server.  
Client applications can access data from TelematicZap on behalf of authenticated users.  
Users can see their registered applications here:  

`http://localhost:8000/o/applications/`

### 1. Register a new client application
To register a new application, a user must navigate to:  
`http://localhost:8000/o/applications/register/`

You should have something like the following:    
`<CLIENT-ID>: JJTqjC4kqnwQOCgH7L4vm3bQoD6gAWFHGdzshzrD`  
`<CLIENT-SECRET>: 4i6KeMoNrlu71EUKPbLmjLtNwLZ98h46L0GglZp9pXxnEEkMhkt5x457dghZsvUcU4oShpVay1qYfJLLoWoh3agbZjecvJHsOMvqAXctX6ro0NuTxX92uf5zgSwOSHT9`  
`<REDIRECT-URI>: http://localhost:8000/noexist/callback`  


### 2. Start the Authorization code flow
`http://localhost:8000/o/authorize/?response_type=code&client_id=<CLIENT-ID>&redirect_uri=<REDIRECT-ID>`

Which should return us the AUTH-CODE by redirecting:
`http://localhost:8000/noexist/callback?code=<AUTH-CODE>`

Now you can get an access-token from the Authorization server
```
curl -X POST \
    -H "Cache-Control: no-cache" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    "http://localhost:8000/o/token/" \
    -d "client_id=<CLIENT-ID>" \
    -d "client_secret=<CLIENT-SECRET>" \
    -d "code=<AUTH-CODE>" \
    -d "redirect_uri=<REDIRECT-URI>" \
    -d "grant_type=authorization_code"
```


which returns  
`{"access_token": "<ACCESS-TOKEN>", "expires_in": 36000, "token_type": "Bearer", "scope": "read write", "refresh_token": "<REFRESH-TOKEN>"}`


You are now ready to make requests to TelematicZap on behalf of a user.


### 3. Access the resources (client application)
```
curl \
    -H "Authorization: Bearer <ACCESS-TOKEN>" \
    -X GET http://localhost:8000/api/hello
```

# The TelematicZap project 

Auto transform telematics data from one format to another.

[![Demo TelematicZap alpha](https://j.gifs.com/vQjqm5.gif)](https://www.youtube.com/watch?v=hKOi9hcCmps)

This is an open-source django project funded by DAPSI NGI, and developed by Konetik.

## Setup
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
  
To access the administration panel, navigate to:

`http://localhost:8000/a`




# Register client applications to use data on TelematicZap
TelematicZap provides the interface of an OAuth 2 Server.  
Client applications can access data from TelematicZap on behalf of authenticated users.  
Users can see their registered applications here:  

`http://localhost:8000/o/applications/`

  
  

## 1. Register a new client application
To register a new application, a user must navigate to:  
`http://localhost:8000/o/applications/register/`

You should have something like the following:    
`<CLIENT-ID>: JJTqjC4kqnwQOCgH7L4vm3bQoD6gAWFHGdzshzrD`  
`<CLIENT-SECRET>: 4i6KeMoNrlu71EUKPbLmjLtNwLZ98h46L0GglZp9pXxnEEkMhkt5x457dghZsvUcU4oShpVay1qYfJLLoWoh3agbZjecvJHsOMvqAXctX6ro0NuTxX92uf5zgSwOSHT9`  
`<REDIRECT-URI>: http://localhost:8000/noexist/callback`  

  
  

## 2. Start the Authorization code flow
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

  
  

## 3. Access the resources (client application)
```
curl \
    -H "Authorization: Bearer <ACCESS-TOKEN>" \
    -X GET http://localhost:8000/data-format/
```

  
  

# MIT License

Copyright 2021 Konetik Deutschland GmbH

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

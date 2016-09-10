# Startup script to run the AKK web service. Will load the flask application
# from app/__init__.py and run it in debug mode. This will create a new HTTP
# server listening on localhost:5000 with all the functionality defined in this
# project.

from app import app
app.run(debug=True)

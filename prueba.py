from microdot import Microdot

app = Microdot()


""""
########### CLIENTE HTTP para comprobar Microdot ############


htmldoc = '''<!DOCTYPE html>
<html>
    <head>
        <title>Microdot Example Page</title>
    </head>
    <body>
        <div>
            <h1>Microdot Example Page</h1>
            <p>Hello from Microdot!</p>
            <p><a href="/ids">Click to obtain the ids</a></p>
            <p><a href="/shutdown">Click to shutdown the server</a></p>
        </div>
    </body>
</html>
'''

@app.route('/') #app es el servidor Microdot y luego en la ruta /
def hello(request):
    return htmldoc, 200, {'Content-Type': 'text/html'}

@app.route('/ids')
def ids(request):
    data = {'name': 'Pablo', 'age': 21}
    return ujson.dumps(data)

@app.route('/shutdown')
def shutdown(request):
    request.app.shutdown() #lo que se hace en el servidor
    return 'The server is shutting down...' #lo que se le manda al cliente y lo que se ve en él
"""

htmldoc = '''<!DOCTYPE html>
<html>
    <head>
        <title>Microdot Example Page</title>
    </head>
    <body>
        <div>
            <h1>Microdot Example Page</h1>
            <p>Hello from Microdot!</p>
            <p><a href="/ids">Click to obtain the ids</a></p>
            <p><a href="/shutdown">Click to shutdown the server</a></p>
        </div>
    </body>
</html>
'''

def funcion():
    
    @app.route('/webhooks') #app es el servidor Microdot y luego en la ruta /
    
    def hello(request):
        return htmldoc, 200, {'Content-Type': 'text/html'}

    @app.route('/webhooks/topic/connections/') #app es el servidor Microdot y luego en la ruta /
    def hello2(request):
        return 'OK', 200

    @app.route('/shutdown')
    def shutdown(request): #DA ERROR SI NO LE PASAS EL ARGUMENTO request
        app.shutdown()
        return 'Shutting down the server...'

    
app.run(port=11001,debug=True)

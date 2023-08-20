from m_asyncio import Microdot

app = Microdot()

@app.route('/')
async def index():
    return 'Hello, world!'

app.run(debug=True)
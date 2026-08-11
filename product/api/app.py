from fastapi import FastAPI
from product.api.routes import router
app = FastAPI(title='Technology Evolution Engine', description='Patents and problems to buildable blueprints.', version='0.1.0')
app.include_router(router)
@app.get('/health')
def health(): return {'status':'ok','engine':'TEE','version':'0.1.0'}

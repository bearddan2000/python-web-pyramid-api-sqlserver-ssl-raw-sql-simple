from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings
# from strategy.cls_chained import Chained
from strategy.cls_raw import Raw

engine = create_engine('{engine}://{username}:{password}@{host}/{db_name}'.format(
        **settings.SQLSERVER
    ), 
    echo=settings.SQLALCHEMY['debug']    
)

session_local = sessionmaker(
    bind=engine,
    autoflush=settings.SQLALCHEMY['autoflush'],
    autocommit=settings.SQLALCHEMY['autocommit']
)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

def get_strategy():
    db = next(get_db())
    return Raw(db)

@view_config(renderer='json')
def hello_world(request):
    return {"hello": "world"}

@view_config(renderer='json')
def get_all(request):
    return get_strategy().all()

@view_config(renderer='json')
def crud(request):
    dog_id  = request.matchdict['dog_id']
    if request.method == 'GET':
        return get_strategy().filter_by(dog_id)
    
    return get_strategy().delete_by(dog_id)

@view_config(renderer='json')
def insert_entry(request):
    dog_breed  = request.matchdict['dog_breed']
    dog_color  = request.matchdict['dog_color']
    return get_strategy().insert_entry(dog_breed, dog_color)

@view_config(renderer='json')
def update_entry(request):
    dog_id  = request.matchdict['dog_id']
    dog_breed  = request.matchdict['dog_breed']
    dog_color  = request.matchdict['dog_color']
    return get_strategy().update_entry(dog_id, dog_breed, dog_color)

if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('smoke_test', '/')
        config.add_route('get', '/dog')
        config.add_route('get_del', '/dog/{dog_id}')
        config.add_route('put', '/dog/{dog_breed}/{dog_color}')
        config.add_route('post', '/dog/{dog_id}/{dog_breed}/{dog_color}')
        config.add_view(hello_world, route_name='smoke_test', renderer='json')
        config.add_view(get_all, route_name='get', renderer='json')
        config.add_view(crud, route_name='get_del', renderer='json')
        config.add_view(insert_entry, route_name='put', renderer='json')
        config.add_view(update_entry, route_name='post', renderer='json')
        config.scan('model')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()

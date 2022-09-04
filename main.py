from sanic import Sanic
from sanic.response import json
from asyncpg import create_pool
import bcrypt
import jwt

from auth import protected

app = Sanic("main")
app.config.SECRET = 'secret_key'


@app.listener('before_server_start')
async def start_database(app, loop):
    connection = "postgres://{user}:{password}@{host}:{port}/{database}".format(
        user='test_user', password='test_user', host='127.0.0.1', port='54322',
        database='test_db'
    )
    app.config['pool'] = await create_pool(
        dsn=connection,
        min_size=10,
        max_size=10,
        max_queries=50000,
        max_inactive_connection_lifetime=300,
        loop=loop
    )


@app.listener('after_server_stop')
async def stop_database(app, loop):
    pool = app.config['pool']
    async with pool.acquire() as connection:
        await connection.close()


@app.route("/admin/")
@protected
async def index(request):
    db = request.app.config['pool']
    async with db.acquire() as conn:
        sql = 'SELECT * FROM Product;'
        products = await conn.fetch(sql)
        for product in products:
            print(dict(product))
    return json({'a': 'b'})


@app.route("/register/", methods=["POST"])
async def register(request):
    login = request.form['login'][0]
    password = bcrypt.hashpw(request.form['password'][0].encode(), bcrypt.gensalt()).decode('utf-8')
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        sql = "INSERT INTO Customer (login, password) VALUES ('{login}', '{password}')".format(
            login=login, password=password
        )
        await conn.execute(sql)
    return json("success")


@app.route("/register/callback/", methods=["GET"])
@protected
async def register_callback(request):
    token = jwt.decode(
        request.token, request.app.config.SECRET, algorithms=["HS256"]
    )
    if not token['active']:
        pool = request.app.config['pool']
        async with pool.acquire() as conn:
            sql = "UPDATE CUSTOMER SET active=True"
            await conn.execute(sql)
    return json('success')


@app.route("/login/", methods=["POST"])
async def login(request):
    try:
        pool = request.app.config['pool']
        async with pool.acquire() as conn:
            sql = "SELECT * FROM Customer WHERE login='{login}'".format(
                login=request.form['login'][0]
            )
            user = await conn.fetch(sql)
            user = dict(user[0])
            valid = bcrypt.checkpw(request.form['password'][0].encode(), user['password'].encode())
            if not valid:
                raise
            token = jwt.encode({'id': user['id'], 'login': user['login'], 'active': user['active'],
                                'admin': user['admin']}, request.app.config.SECRET, algorithm="HS256")
            return json(token)
    except:
        return json("incorrect login or password", status=400)


@app.route("/api/bill/", methods=["GET"])
@protected
async def get_bill(request):
    pass


@app.route("/api/product/", methods=["GET"])
@protected
async def get_product(request):
    pool = request.app.config['pool']
    product_list = []
    async with pool.acquire() as conn:
        sql = 'SELECT * FROM Product;'
        products = await conn.fetch(sql)
        for product in products:
            product_list.append(dict(product))
    return json(product_list)


@app.route("/admin/api/product/add/", methods=["POST"])
@protected
async def add_product(request):
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        sql = "INSERT INTO Product (name, description, price) VALUES ('{name}', '{description}', '{price}')".format(
            name=request.form['name'][0], description=request.form['description'][0], price=float(request.form['price'][0])
        )
        await conn.execute(sql)
    return json('create success')


@app.route("/admin/api/product/delete/<id:int>/", methods=["GET"])
@protected
async def delete_product(request, id):
    pool = request.app.config['pool']
    async with pool.acquire() as conn:
        sql = "DELETE FROM Product WHERE id={id}".format(
            id=id)
        await conn.execute(sql)
    return json('delete success')


@app.route("/admin/api/product/manage/<id:int>/", methods=["POST"])
@protected
async def manage_product(request, id):
    pool = request.app.config['pool']
    sql = "UPDATE Product SET "
    for i in request.form:
        if i == 'price':
            sql += i + '=' + request.form[i][0] + ', '
        else:
            sql += i + '=' + "'" + request.form[i][0] + "'" + ', '
    sql = sql[:-2] + " WHERE id={id}".format(id=id)
    async with pool.acquire() as conn:
        await conn.execute(sql)
    print(sql)
    return json('manage success')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, dev=True)

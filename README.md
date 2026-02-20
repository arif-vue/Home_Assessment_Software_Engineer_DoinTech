# DoinTech Trading Signal Service
a backend service that receives trading signals and routes them to a broker account.Built with Django and Django Channels.

---
## What it does
you send a signal like "BUY EURUSD" to the service.It parses the signal,finds your broker account,places the order,and updates the order status in real time via WebSocket.

---
## Setup

**Clone the repo and go into the folder**
```
git clone https://github.com/arif-vue/TradeWire.git
cd TradeWire
```
**Create and activate virtual environment**
```
python3 -m venv venv
source venv/bin/activate
```
**Install dependencies**
```
pip install -r requirements.txt
```
**Run migrations**
```
python manage.py makemigrations
python manage.py migrate
```
**Create a superuser (for admin panel)**
```
python manage.py createsuperuser
```
**Start the server**
```
python manage.py runserver
```
Server runs at `http://localhost:8000`

---
## Postman
Import the file `Doin Tech.postman_collection.json` into Postman.All requests are already set up with variables. Just register, copy your token, set it in the collection variable `token`, and you are ready.

**How to set the token on each request in Postman:**

First go to the Authorization** tab of any protected request. You will see two things to set:

1. Select type **Bearer Token** and paste your token in the token field
2. Then also add an **API Key** entry:
   - Key: `Authorization`
   - Value: `Token <paste your token here>`
   - Add to: `Header`

the reason you need the API Key step is that Django reads the header as `Token <key>` not `Bearer <key>`.so the API Key entry is what actually sends the correct format to the server.

---
## How to use the API

**1.Register**
```
POST /auth/register
{
  "username": "arif",
  "password": "mypassword123"
}
```
You get back a token. Copy it.

**2.Login**
```
POST /auth/token
{
  "username": "arif",
  "password": "mypassword123"
}
```
You get back a token. Copy it.

**3.Link your broker account**
```
POST /accounts
Authorization: Token <your_token>
{
  "account_id": "MT12345",
  "broker_name": "MetaTrader",
  "api_key": "your-broker-api-key"
}
```
**4.Send a trading signal**
```
POST /webhook/receive-signal
Authorization: Token <your_token>
{
  "signal": "BUY EURUSD @1.0860\nSL 1.0850\nTP 1.0890"
}
```
Signal format:
- First line: action (BUY or SELL) + instrument + optional price with @
- SL line: stop loss price
- TP line: take profit price

For BUY, SL must be lower than TP. For SELL it is the opposite. If the signal is wrong you get back an error explaining what is missing or invalid.

**5.Check your orders**
```
GET /orders
Authorization: Token <your_token>
```
**6.Check one order**
```
GET /orders/<order_id>
Authorization: Token <your_token>
```
**7.See your stats**
```
GET /analytics
Authorization: Token <your_token>
```
---
## How the webhook works
when a signal comes in the service immediately returns 200 with an order_id. In the background it saves the order with status `pending`, then after 5 seconds changes it to `executed`.at that point it sends a WebSocket message to anyone connected at `ws://localhost:8000/ws/orders`.

WebSocket message looks like this:
```json
{
  "type": "order.executed",
  "order_id": "e11c21d2-...",
  "instrument": "EURUSD",
  "entry_price": 1.086
}
```
---
## Design notes

i kept the code simple on purpose.Each view does one thing.The signal parser is in `services.py` so it is easy to test separately from the view.the broker execution is mocked with a function that logs and returns a fake order ID — swapping in a real broker API later would only change that one function.

the order status simulation uses a Python thread with a 5 second sleep.for production this should be replaced with Celery.the WebSocket uses Django Channels with an in-memory channel layer which is fine for development but Redis should be used in production.

one thing i would do differently with more time is add proptr error logging to a file so you can trace what happened to each signal.

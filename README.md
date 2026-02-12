This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the production server:

Frontend:
```bash
npm run start
```
Backend:
run python .\FlaskApp.py 

Now open [http://localhost:3000](http://localhost:3000) with your browser to see the result.




## System higher level hierachy

<img width="976" height="910" alt="image" src="https://github.com/user-attachments/assets/c92759b1-0b15-461e-9442-9a1315360ac0" />





# UI views and functionalities


## Home page

<img width="1906" height="916" alt="image" src="https://github.com/user-attachments/assets/fa30b695-cbaf-4de6-8e05-f808523118bc" />

Alarms are shown on the right side bar with option that user can show only alarms from today.

## Live streamer controlling

<img width="1893" height="909" alt="image" src="https://github.com/user-attachments/assets/8bab578e-933f-423c-a8b5-dd5249f6f101" />

Start watchliststreamer with input tickers. Show database last rows in the table.

## Order and position management

<img width="1907" height="924" alt="image" src="https://github.com/user-attachments/assets/ff9b62d1-fd6b-47eb-b5b8-d0595d6c5d9b" />

There is Alpaca API for Tradeview integration where user can place stop level manually. Order will show here. Another method is automatic generated
order when entry is triggered.
Below there is open position management table. It includes request exit button which will tell to code that if there is certain trigger this position will be
closed automatically using market order in IBKR TWS API.

## Market scanners

<img width="1911" height="925" alt="image" src="https://github.com/user-attachments/assets/46cd9b08-f00a-499e-9c5e-08a722984713" />

Scanning real time market with certain parameters. The most extreme moves should pop up.


## TODO:
- Backend to FaskAPI and making it solid asynchronous with IB client
- Monthly view on the home page
- Risk levels order management improvments (add to order, 




## Endpoint testing script

POST request 

$uri = "http://localhost:8080/api/portfoliomanager"

$body = @{
    Symbol = "MU"
    Alarm  = "endofday_exit"
    Date   = "2026-01-15"
    Time   = "10:12:00"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri $uri `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

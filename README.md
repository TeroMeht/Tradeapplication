This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## System higher level hierachy

<img width="976" height="910" alt="image" src="https://github.com/user-attachments/assets/c92759b1-0b15-461e-9442-9a1315360ac0" />











## Endpoint testing script

POST request 

$uri = "http://localhost:8080/api/portfoliomanager"

$body = @{
    Symbol = "NVDA"
    Alarm  = "euforia"
    Date   = "2026-01-15"
    Time   = "10:12:00"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri $uri `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

# EnterTheMatrix

A Matrix-themed Flask demo app for showcasing Microsoft Entra ID
authentication and Conditional Access policies.

## What it does
Logs users in via Entra ID (MSAL authorization code flow) and displays
their identity claims. Built to demo App Registration, Enterprise Apps,
and Conditional Access behavior.

## Use case
Toggle CA policies (MFA, compliant device, named location, sign-in risk)
and observe the effect on login and in Entra sign-in logs.

## Setup
Requires env vars: CLIENT_ID, CLIENT_SECRET, TENANT_ID, FLASK_SECRET (optional).
Redirect URI: /auth/redirect
Scope: User.Read

## Routes
- /          home / login
- /login     start auth flow
- /claims    view issued ID token claims
- /health    liveness check
- /logout    clear session + Entra logout

## How to run
Here's the full flow to run and demo it.

1. Register the app in Entra ID

In Azure portal → Entra ID → App registrations → New registration:

Set a name
Add a redirect URI of type Web: https://<your-host>/auth/redirect
Under Certificates & secrets, create a client secret
Grab the Application (client) ID, Directory (tenant) ID, and the secret value

2. Set environment variables

bash
export CLIENT_ID="<application-client-id>"
export CLIENT_SECRET="<client-secret-value>"
export TENANT_ID="<directory-tenant-id>"
export FLASK_SECRET="<any-random-string>"   # optional
export PORT=8000                             # optional

3. Install and run

bash
pip install flask msal
python app.py

App listens on 0.0.0.0:8000.

4. HTTPS is required

The code hardcodes _scheme="https" for the redirect URI, so Entra will redirect to an https:// URL. Running bare http://localhost won't match. Options: put it behind a tunnel (ngrok, Cloudflare Tunnel) or a reverse proxy that terminates TLS. Whatever host you use must match the redirect URI you registered in step 1.

5. Use it

Go to your host in a browser → click "Login with Entra ID" → authenticate → you land on the authenticated screen showing your claims.

6. Demo Conditional Access

This is what it's built for:

Create a CA policy in Entra targeting this app (now visible under Enterprise applications)
Require MFA, or a compliant device, or restrict to a named location
Try logging in again and watch it get challenged or blocked
Check Entra → Sign-in logs to see the policy applied

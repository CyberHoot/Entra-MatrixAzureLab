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

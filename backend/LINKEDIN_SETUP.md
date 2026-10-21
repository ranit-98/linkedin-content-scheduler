# LinkedIn Developer App Setup

This guide explains how to obtain the following backend settings for real LinkedIn sign-in and
member posting:

```env
LINKEDIN_CLIENT_ID=your-client-id
LINKEDIN_CLIENT_SECRET=your-client-secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/auth/linkedin/callback
LINKEDIN_API_VERSION=202609
```

> For a local demo that does not contact LinkedIn, set `LINKEDIN_MOCK_MODE=true` instead. Client
> credentials are only required when `LINKEDIN_MOCK_MODE=false`.

## 1. Create a LinkedIn developer app

1. Sign in to the [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps).
2. Select **Create app**.
3. Enter the app name and associate it with a LinkedIn Page.
4. Enter a privacy-policy URL, upload an app logo, accept the terms, and create the app.
5. Complete the LinkedIn Page association verification if LinkedIn requests it. A Page
   administrator may need to approve the association.

LinkedIn's official instructions are available in
[Create a new app for a LinkedIn Page](https://www.linkedin.com/help/linkedin/answer/a1667239)
and [Accessing LinkedIn APIs](https://www.linkedin.com/help/linkedin/answer/a525039).

## 2. Request the required products

Open the app's **Products** tab and request/add both of these products:

1. **Sign In with LinkedIn using OpenID Connect**
   - Provides the `openid` and `profile` permissions used to identify the connected member.
2. **Share on LinkedIn**
   - Provides the `w_member_social` permission used to publish a post for that member.

The app requests exactly these scopes:

```text
openid profile w_member_social
```

Product access may not be instantaneous. In the **Auth** tab, confirm that all three permissions
appear under the OAuth scopes before testing. See LinkedIn's official
[OpenID Connect guide](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/sign-in-with-linkedin-v2)
and [Share on LinkedIn guide](https://learn.microsoft.com/en-us/linkedin/consumer/integrations/self-serve/share-on-linkedin).

## 3. Register the callback URL

In the app's **Auth** tab, find **OAuth 2.0 settings** or **Authorized redirect URLs for your app**.
Add this exact local URL:

```text
http://localhost:8000/api/v1/auth/linkedin/callback
```

The value must match `LINKEDIN_REDIRECT_URI` exactly, including the scheme, hostname, port, path,
and trailing-slash choice. LinkedIn documents the full process in its
[3-legged OAuth guide](https://learn.microsoft.com/en-us/linkedin/shared/authentication/authorization-code-flow?tabs=HTTPS1).
LinkedIn also provides an official
[localhost OAuth sample](https://learn.microsoft.com/en-us/linkedin/shared/authentication/sample-applications).

For production, register the public HTTPS callback instead, for example:

```text
https://api.example.com/api/v1/auth/linkedin/callback
```

Use separate LinkedIn apps for local development and production when possible.

## 4. Copy the Client ID and Client Secret

In the app's **Auth** tab:

1. Copy **Client ID** into `LINKEDIN_CLIENT_ID`.
2. Reveal/copy **Primary Client Secret** into `LINKEDIN_CLIENT_SECRET`.
3. Never place the secret in frontend code or any `NEXT_PUBLIC_*` setting.

Edit `backend/.env`:

```env
LINKEDIN_CLIENT_ID=copy-client-id-here
LINKEDIN_CLIENT_SECRET=copy-client-secret-here
LINKEDIN_REDIRECT_URI=http://localhost:8000/api/v1/auth/linkedin/callback
LINKEDIN_API_VERSION=202609
LINKEDIN_MOCK_MODE=false
```

Do not commit `backend/.env`. If a secret is exposed, generate a new secret in the LinkedIn
Developer Portal and replace the old one immediately.

## 5. Choose the LinkedIn API version

`LINKEDIN_API_VERSION` is sent as the `LinkedIn-Version` header for the versioned Posts API. The
format is `YYYYMM`; it is not a client credential. At the time this guide was updated (October
2026), LinkedIn lists `202609` as its latest version, so the repository default is:

```env
LINKEDIN_API_VERSION=202609
```

Before deploying, check LinkedIn's
[Marketing API versioning page](https://learn.microsoft.com/en-us/linkedin/marketing/versioning)
and [recent API changes](https://learn.microsoft.com/en-us/linkedin/marketing/integrations/recent-changes).
Update the value when the configured version approaches its sunset date. The Posts API requires
this header; an unsupported version can produce `426 Upgrade Required`.

## 6. Restart and connect

After changing `.env`, recreate the backend services so they receive the new values:

```bash
cd backend
docker compose up -d --build --force-recreate
```

Keep the frontend running, then either select **Connect LinkedIn** in the UI at
<http://localhost:3000>, or open the authorization endpoint directly:

<http://localhost:8000/api/v1/auth/linkedin/authorize>

LinkedIn should show its consent page and then redirect to the registered backend callback. Check
the saved connection in the UI or with:

```bash
curl http://localhost:8000/api/v1/connections
```

## Troubleshooting

- **Redirect URI mismatch:** Copy the callback URL from this guide into both the LinkedIn portal
  and `.env`; do not add a trailing slash to only one of them.
- **Invalid scope / unauthorized scope:** Confirm both products are approved and that `openid`,
  `profile`, and `w_member_social` appear in the app's Auth tab.
- **Invalid client:** Recopy the Client ID and Client Secret, then recreate the backend containers.
- **The app still creates a demo connection:** Set `LINKEDIN_MOCK_MODE=false` and restart the
  backend.
- **`426 Upgrade Required`:** Select a supported `YYYYMM` value from LinkedIn's versioning page.
- **The callback returns an error:** Inspect the API logs with
  `docker compose logs --tail=200 api` from the `backend` directory.


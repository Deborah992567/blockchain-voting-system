import requests
from app.utils.logger import logger as base_logger
from app.config import settings

logger = base_logger.bind(context="auth.oauth")


def verify_google_token(id_token: str) -> dict:
    """Verify a Google ID token using Google's tokeninfo endpoint.
    Returns token payload dict on success, raises RuntimeError on failure."""
    logger.info("Verifying Google ID token")
    try:
        resp = requests.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": id_token}, timeout=5)
    except Exception:
        logger.exception("Failed to contact Google tokeninfo")
        raise RuntimeError("Failed to verify Google token")

    if resp.status_code != 200:
        logger.warning("Google tokeninfo returned non-200", status_code=resp.status_code)
        raise RuntimeError("Invalid Google token")

    data = resp.json()
    # expected fields: sub (user id), email, email_verified
    if "sub" not in data:
        logger.warning("Google token missing subject")
        raise RuntimeError("Invalid Google token payload")

    logger.debug("Google token verified", sub=data.get("sub"), email=data.get("email"))
    return data


def verify_github_token(access_token: str) -> dict:
    """Verify a GitHub access token by calling the user API.
    Returns dict with at least 'id' and possibly 'email'."""
    logger.info("Verifying GitHub access token")
    headers = {"Authorization": f"token {access_token}", "Accept": "application/vnd.github+json"}
    try:
        resp = requests.get("https://api.github.com/user", headers=headers, timeout=5)
    except Exception:
        logger.exception("Failed to contact GitHub API")
        raise RuntimeError("Failed to verify GitHub token")

    if resp.status_code != 200:
        logger.warning("GitHub user endpoint returned non-200", status_code=resp.status_code)
        raise RuntimeError("Invalid GitHub token")

    data = resp.json()

    # If email not present, fetch emails endpoint
    if not data.get("email"):
        try:
            emails_resp = requests.get("https://api.github.com/user/emails", headers=headers, timeout=5)
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                if primary:
                    data["email"] = primary.get("email")
        except Exception:
            logger.exception("Failed to fetch GitHub user emails")

    logger.debug("GitHub token verified", id=data.get("id"), email=data.get("email"))
    return data


def exchange_google_code(code: str, redirect_uri: str):
    logger.info("Exchanging Google code for tokens")
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.error("Google OAuth client not configured")
        raise RuntimeError("Google OAuth not configured")

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    try:
        resp = requests.post(token_url, data=payload, timeout=5)
    except Exception:
        logger.exception("Failed to contact Google token endpoint")
        raise RuntimeError("Failed to exchange Google code")

    if resp.status_code != 200:
        logger.warning("Google token exchange failed", status_code=resp.status_code, body=resp.text)
        raise RuntimeError("Invalid Google code")

    token_data = resp.json()
    id_token = token_data.get("id_token")
    if not id_token:
        logger.warning("No id_token in Google token response")
        raise RuntimeError("Google did not return id_token")

    return verify_google_token(id_token)


def exchange_github_code(code: str, redirect_uri: str | None = None):
    logger.info("Exchanging GitHub code for access token")
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        logger.error("GitHub OAuth client not configured")
        raise RuntimeError("GitHub OAuth not configured")

    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code
    }
    headers = {"Accept": "application/json"}
    try:
        resp = requests.post(token_url, data=payload, headers=headers, timeout=5)
    except Exception:
        logger.exception("Failed to contact GitHub token endpoint")
        raise RuntimeError("Failed to exchange GitHub code")

    if resp.status_code != 200:
        logger.warning("GitHub token exchange failed", status_code=resp.status_code, body=resp.text)
        raise RuntimeError("Invalid GitHub code")

    data = resp.json()
    access_token = data.get("access_token")
    if not access_token:
        logger.warning("No access_token in GitHub token response", body=data)
        raise RuntimeError("GitHub did not return access token")

    return verify_github_token(access_token)

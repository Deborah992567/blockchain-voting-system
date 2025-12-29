import requests
from app.utils.logger import logger as base_logger

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

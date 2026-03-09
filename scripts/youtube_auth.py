"""
One-time YouTube OAuth setup.
Run this once to authorize your PERSONAL YouTube account for uploads.

Prerequisites:
1. Go to console.cloud.google.com (personal account)
2. Create project → Enable "YouTube Data API v3"
3. Create OAuth 2.0 credentials (Desktop Application)
4. Download client_secret.json → place in project root

Usage:
  python scripts/youtube_auth.py          # First-time setup
  python scripts/youtube_auth.py --force  # Re-authorize (refresh token expired)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent
CLIENT_SECRET = ROOT / "client_secret.json"
TOKEN_FILE = ROOT / "token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
           "https://www.googleapis.com/auth/youtube"]


def setup(force=False):
    if not CLIENT_SECRET.exists():
        print("\n❌ client_secret.json not found!")
        print("\nSetup steps:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Sign in with your PERSONAL Google account")
        print("  3. Create a new project: 'Shorts Factory'")
        print("  4. Go to APIs & Services → Enable 'YouTube Data API v3'")
        print("  5. Go to Credentials → Create OAuth 2.0 Client ID (Desktop)")
        print("  6. Download the JSON → rename to 'client_secret.json'")
        print(f"  7. Place it in: {ROOT}/")
        print("  8. Run this script again")
        return

    if TOKEN_FILE.exists() and not force:
        print(f"\n⚠️  token.json already exists at {TOKEN_FILE}")
        print(f"   To re-authorize, run: python scripts/youtube_auth.py --force\n")
        return

    from google_auth_oauthlib.flow import InstalledAppFlow

    if force and TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print("\n🗑️  Deleted old token.json")

    print("\n🔐 Starting YouTube OAuth flow...")
    print("   A browser window will open — sign in with your PERSONAL account\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    credentials = flow.run_local_server(port=8081)

    TOKEN_FILE.write_text(credentials.to_json())
    print(f"\n✅ Authorization complete! Token saved to {TOKEN_FILE}")
    print("   You can now use the upload pipeline with your personal YouTube account.")
    print("\n💡 TIP: To prevent tokens from expiring every 7 days, go to:")
    print("   https://console.cloud.google.com/apis/credentials/consent")
    print("   and click 'PUBLISH APP' to move from Testing → Production.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube OAuth setup")
    parser.add_argument("--force", action="store_true",
                        help="Force re-authorization (use when token is expired/revoked)")
    args = parser.parse_args()
    setup(force=args.force)

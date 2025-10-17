#!/usr/bin/env python3
"""
Simple test script to diagnose Reddit authentication issues.
"""

import os
import praw

# Get credentials
client_id = os.getenv('REDDIT_CLIENT_ID')
client_secret = os.getenv('REDDIT_CLIENT_SECRET')
username = os.getenv('REDDIT_USERNAME')
password = os.getenv('REDDIT_PASSWORD')
user_agent = os.getenv('REDDIT_USER_AGENT', 'test:v1.0:script')

print("=" * 80)
print("Reddit Authentication Test")
print("=" * 80)
print(f"Client ID: {client_id[:10]}..." if client_id else "Client ID: MISSING")
print(f"Username: {username}")
print(f"User Agent: {user_agent}")
print("=" * 80)

try:
    print("\n1. Creating Reddit instance...")
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password
    )
    print("   ✓ Reddit instance created")
    
    print("\n2. Testing authentication by getting user info...")
    me = reddit.user.me()
    print(f"   ✓ Authenticated as: {me.name}")
    print(f"   ✓ Link karma: {me.link_karma}")
    print(f"   ✓ Comment karma: {me.comment_karma}")
    
    print("\n3. Testing read access...")
    subreddit = reddit.subreddit('homeassistant')
    print(f"   ✓ Can read r/homeassistant (subscribers: {subreddit.subscribers})")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Authentication is working!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nFull traceback:")
    import traceback
    traceback.print_exc()

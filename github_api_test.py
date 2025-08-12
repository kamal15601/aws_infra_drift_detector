#!/usr/bin/env python3
"""
GitHub Repository API Data Fetcher
Fetches repository information from GitHub API
"""

import requests
import json
from datetime import datetime

def get_github_repo_data(repo_url):
    """
    Fetch repository data from GitHub API
    """
    try:
        # Add headers to simulate browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Make request to GitHub API
        response = requests.get(repo_url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Raw response: {response.text[:500]}...")
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Print formatted repository information
            print("=" * 60)
            print(f"REPOSITORY: {data.get('full_name', 'N/A')}")
            print("=" * 60)
            print(f"Name: {data.get('name', 'N/A')}")
            print(f"Description: {data.get('description', 'N/A')}")
            print(f"Owner: {data.get('owner', {}).get('login', 'N/A')}")
            print(f"Private: {data.get('private', 'N/A')}")
            print(f"Fork: {data.get('fork', 'N/A')}")
            print(f"Stars: {data.get('stargazers_count', 'N/A')}")
            print(f"Forks: {data.get('forks_count', 'N/A')}")
            print(f"Language: {data.get('language', 'N/A')}")
            print(f"Size: {data.get('size', 'N/A')} KB")
            print(f"Default Branch: {data.get('default_branch', 'N/A')}")
            print(f"Created: {data.get('created_at', 'N/A')}")
            print(f"Updated: {data.get('updated_at', 'N/A')}")
            print(f"Clone URL: {data.get('clone_url', 'N/A')}")
            print(f"SSH URL: {data.get('ssh_url', 'N/A')}")
            print(f"Has Issues: {data.get('has_issues', 'N/A')}")
            print(f"Has Wiki: {data.get('has_wiki', 'N/A')}")
            print(f"Has Pages: {data.get('has_pages', 'N/A')}")
            
            # Check permissions
            permissions = data.get('permissions', {})
            if permissions:
                print("\nPermissions:")
                print(f"  Admin: {permissions.get('admin', 'N/A')}")
                print(f"  Push: {permissions.get('push', 'N/A')}")
                print(f"  Pull: {permissions.get('pull', 'N/A')}")
            
            return data
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden - API rate limit exceeded or access denied")
            print("Response:", response.text)
            return None
            
        elif response.status_code == 404:
            print("❌ 404 Not Found - Repository not found or is private")
            return None
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return None

def check_repository_access(repo_url):
    """
    Check if repository is accessible and what permissions are available
    """
    print(f"🔍 Checking repository access...")
    print(f"URL: {repo_url}")
    print(f"Time: {datetime.now().isoformat()}")
    print()
    
    # Test multiple endpoints
    test_urls = [
        repo_url,  # Original API endpoint
        repo_url.replace('/repos/', '/repos/').rstrip('/'),  # Clean URL
        f"https://github.com/kamal15601/aws_infra_drift_detector",  # Direct GitHub URL
        f"https://api.github.com/users/kamal15601",  # User endpoint
        f"https://api.github.com/users/kamal15601/repos"  # User repos endpoint
    ]
    
    for url in test_urls:
        print(f"\n🔗 Testing: {url}")
        try:
            headers = {
                'User-Agent': 'GitHub-API-Test/1.0',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get(url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                if 'api.github.com' in url:
                    try:
                        data = response.json()
                        if isinstance(data, list):
                            print(f"   Found {len(data)} items")
                        else:
                            print(f"   Repository: {data.get('full_name', 'Unknown')}")
                    except:
                        print("   Valid response but not JSON")
                else:
                    print("   GitHub page accessible")
            else:
                print(f"   Error: {response.text[:100]}")
                
        except Exception as e:
            print(f"   Exception: {e}")
    
    # Now test the original function
    print(f"\n{'='*60}")
    print("DETAILED API TEST:")
    print(f"{'='*60}")
    
    data = get_github_repo_data(repo_url)
    
    if data:
        print("\n✅ Repository is accessible!")
        
        # Check if it's a public repository
        if not data.get('private', True):
            print("✅ Repository is PUBLIC - should be accessible to Azure")
        else:
            print("⚠️ Repository is PRIVATE - requires authentication")
            
        return True
    else:
        print("\n❌ Repository is NOT accessible!")
        print("\n🔧 POSSIBLE SOLUTIONS:")
        print("1. Check if repository name is spelled correctly")
        print("2. Verify repository is public")
        print("3. Check GitHub username spelling")
        print("4. Try using Personal Access Token")
        return False

if __name__ == "__main__":
    repo_url = "https://api.github.com/repos/kamal15601/aws_infra_drift_detector/"
    check_repository_access(repo_url)

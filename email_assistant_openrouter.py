import os
import base64
import json
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests

# Load your API keys from .env file
load_dotenv()

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Get OpenRouter API key from .env
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Test if API key loaded correctly
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in .env file!")
    print("Please add: OPENROUTER_API_KEY=your-key-here")
    exit(1)
else:
    print("✅ OpenRouter API key loaded successfully")

def call_openrouter(prompt, model="openrouter/free"):
    """Call OpenRouter API with a prompt using free models."""
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return f"[Error: API call failed]"

def authenticate_gmail():
    """Handles logging into Gmail securely"""
    creds = None
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        print("✅ Found saved token, using existing login")
    
    if not creds or not creds.valid:
        print("🔐 Need to log into Google...")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            print("✅ Refreshed expired token")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Logged in successfully")
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("💾 Saved token for next time")
    
    return creds

def extract_email_body(payload):
    """Gets the actual text content from an email"""
    body = ''
    
    if 'parts' not in payload:
        if 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        return body
    
    for part in payload['parts']:
        if part['mimeType'] == 'text/plain':
            if 'data' in part['body']:
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                break
        elif 'parts' in part:
            body = extract_email_body(part)
            if body:
                break
    
    if not body:
        body = "[Could not extract email body]"
    
    return body

def fetch_recent_emails(service, max_results=3):
    """Gets recent emails from your inbox"""
    print(f"📧 Fetching up to {max_results} recent emails...")
    
    results = service.users().messages().list(
        userId='me', 
        maxResults=max_results,
        labelIds=['INBOX']
    ).execute()
    
    messages = results.get('messages', [])
    print(f"📬 Found {len(messages)} emails")
    
    if not messages:
        print("No emails found!")
        return []
    
    emails = []
    
    for i, msg in enumerate(messages, 1):
        print(f"  📨 Fetching email {i}/{len(messages)}...")
        
        msg_data = service.users().messages().get(
            userId='me', 
            id=msg['id'],
            format='full'
        ).execute()
        
        headers = msg_data['payload'].get('headers', [])
        
        def get_header(name):
            return next((h['value'] for h in headers if h['name'] == name), 'Not found')
        
        subject = get_header('Subject')
        sender = get_header('From')
        date = get_header('Date')
        body = extract_email_body(msg_data['payload'])
        body = ' '.join(body.split())[:1000]
        
        emails.append({
            'id': msg['id'],
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body
        })
    
    print("✅ All emails fetched successfully")
    return emails

def summarize_with_openrouter(email):
    """Summarize email using OpenRouter free model"""
    print("  🤖 Generating summary with OpenRouter...")
    
    prompt = f"""Summarize this email in 1-2 sentences. Focus on what action is needed.

From: {email['sender']}
Subject: {email['subject']}
Content: {email['body']}

Summary:"""
    
    summary = call_openrouter(prompt)
    print(f"  ✅ Summary generated")
    return summary

def generate_draft_reply(email):
    """Generate reply draft using OpenRouter free model"""
    print("  ✏️ Generating draft reply...")
    
    prompt = f"""Write a professional draft reply to this email.

Original Email:
Subject: {email['subject']}
From: {email['sender']}
Content: {email['body']}

Instructions:
- If this doesn't need a reply (spam, newsletter), just say "No reply needed"
- Otherwise, write a brief, polite reply (under 100 words)
- Start with "Re: {email['subject']}" as subject line
- Sign off as "[Your Name]"

Draft Reply:"""
    
    reply = call_openrouter(prompt)
    print(f"  ✅ Reply generated")
    return reply

def save_results_to_file(emails, summaries, replies):
    """Saves results to JSON file"""
    results = []
    for email, summary, reply in zip(emails, summaries, replies):
        results.append({
            'sender': email['sender'],
            'subject': email['subject'],
            'date': email['date'],
            'summary': summary,
            'draft_reply': reply,
            'needs_reply': 'No reply needed' not in reply
        })
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'email_summaries_{timestamp}.json'
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to {filename}")
    return filename

def display_results(emails, summaries, replies):
    """Prints results nicely"""
    print("\n" + "="*70)
    print("📊 YOUR EMAIL SUMMARY REPORT")
    print("="*70)
    
    for i, (email, summary, reply) in enumerate(zip(emails, summaries, replies), 1):
        print(f"\n📧 EMAIL #{i}")
        print(f"📨 From: {email['sender'][:80]}")
        print(f"📌 Subject: {email['subject'][:80]}")
        print(f"\n📝 SUMMARY: {summary}")
        print(f"\n✏️ DRAFT REPLY:")
        
        if "No reply needed" in reply:
            print(f"   💤 {reply}")
        else:
            for line in reply.split('\n'):
                print(f"   {line}")
        
        print("\n" + "-"*70)

def main():
    print("\n" + "="*60)
    print("🤖 EMAIL ASSISTANT with OpenRouter (Free Tier)")
    print("="*60 + "\n")
    
    print("Step 1/4: Connecting to Gmail...")
    try:
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail connected!\n")
    except Exception as e:
        print(f"❌ Failed to connect to Gmail: {e}")
        print("\nMake sure credentials.json is in the same folder!")
        return
    
    print("Step 2/4: Fetching your emails...")
    emails = fetch_recent_emails(service, max_results=3)
    
    if not emails:
        print("No emails to process.")
        return
    
    print(f"✅ Found {len(emails)} emails to process\n")
    
    print("Step 3/4: Analyzing emails with OpenRouter...")
    print("-" * 50)
    
    summaries = []
    replies = []
    
    for i, email in enumerate(emails, 1):
        print(f"\n📧 Processing email {i}/{len(emails)}")
        print(f"   From: {email['sender'][:50]}")
        print(f"   Subject: {email['subject'][:50]}")
        
        summary = summarize_with_openrouter(email)
        summaries.append(summary)
        
        reply = generate_draft_reply(email)
        replies.append(reply)
        
        print(f"   ✅ Done with email {i}")
    
    print("\nStep 4/4: Generating report...")
    display_results(emails, summaries, replies)
    
    filename = save_results_to_file(emails, summaries, replies)
    
    print("\n" + "="*60)
    print("✅ ALL DONE!")
    print("="*60)
    print(f"\n📁 Results saved to: {filename}")
    print("\n💡 TIPS:")
    print("   - Free models work well for summarization")
    print("   - To run again: python email_assistant_openrouter.py")
    print("   - Check the JSON file for saved summaries")

if __name__ == "__main__":
    main()
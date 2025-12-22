import requests
import csv
import sys
import os
from datetime import datetime

def scrape_github_issues():
    all_issues = []
    page = 1
    per_page = 100
    

    os.makedirs('issues_text', exist_ok=True)
    
    while True:
        url = "https://api.github.com/search/issues"
        params = {
            'q': 'repo:Qiskit/qiskit-aer is:issue label:bug created:2023-01-01..2025-11-19',
            'per_page': per_page,
            'page': page
        }
        
        print(f"Fetching page {page}", file=sys.stderr)
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error: {response.status_code}", file=sys.stderr)
            break
        
        data = response.json()
        issues = data.get('items', [])
        
        if not issues:
            break
        
        for issue in issues:
            issue_number = str(issue['number'])
            
            all_issues.append({
                'Project': 'Qiskit/qiskit-aer',
                'IssueID': issue_number,
                'URL': issue['html_url'],
                'Title': issue['title'],
                'Status': issue['state'],
                'CreatedAt': issue['created_at']
            })
            

            body = issue.get('body', '')
            if body:
                filename = f"issues_text/{issue_number}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(body)
                print(f"  Saved issue #{issue_number}", file=sys.stderr)
        
        print(f"Found {len(issues)} issues on page {page} (total so far: {len(all_issues)})", file=sys.stderr)
        

        if len(issues) < per_page:
            break
        
        page += 1
    
    return all_issues

def write_csv(issues, filename='github_issues.csv'):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Project', 'IssueID', 'URL', 'Title', 'Status', 'CreatedAt'])
        writer.writeheader()
        writer.writerows(issues)

if __name__ == '__main__':
    issues = scrape_github_issues()
    write_csv(issues)
    print(f"Total issues scraped: {len(issues)}", file=sys.stderr)
    print("CSV file created: github_issues.csv", file=sys.stderr)
    print("Issue texts saved in: issues_text/", file=sys.stderr)

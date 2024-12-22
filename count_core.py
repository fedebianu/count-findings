from github import Github
from collections import defaultdict

SEVERITY_LABELS = ['Critical', 'High', 'Medium', 'Low', 'Gas', 'Informational']

class CountCore:
    def __init__(self, token, sr, domains, on_progress=None):
        self.token = token
        self.sr = sr
        self.domains = domains if isinstance(domains, list) else domains.split('\n')
        self.on_progress = on_progress or print
        
        # Data tracking
        self.total_counts = defaultdict(int)
        self.repo_counts = defaultdict(lambda: defaultdict(int))
        self.domain_mapping = {}
        self.domain_counts = defaultdict(lambda: defaultdict(int))
        self.is_running = False
    
    def get_repos_for_domain(self, github, domain):
        repos = set()
        self.on_progress(f"Searching repositories in {domain}...")
        
        try:
            query = f'author:{self.sr} org:{domain} is:issue'
            issues = github.search_issues(query)
            for issue in issues:
                repo_name = issue.repository.full_name
                repos.add(repo_name)
                self.domain_mapping[repo_name] = domain
        except Exception as e:
            self.on_progress(f"Error searching in {domain}: {str(e)}")
        
        return repos

    def process_repository(self, github, repo_name):
        try:
            self.on_progress(f"Processing repository: {repo_name}")
            issues_list = github.get_repo(repo_name).get_issues(state='open')
            
            for i in range(issues_list.totalCount//30, -1, -1):
                if not self.is_running:
                    return
                page = issues_list.get_page(i)
                page.reverse()
                for issue in page:
                    if issue.user.login != self.sr:
                        continue
                        
                    if issue.pull_request is None:
                        severity_labels_in_issue = [
                            label.name for label in issue.labels 
                            if label.name in SEVERITY_LABELS
                        ]
                        
                        if len(severity_labels_in_issue) != 1:
                            self.on_progress(f"Warning: Issue {issue.html_url} has {len(severity_labels_in_issue)} severity labels")
                            continue
                        
                        label = severity_labels_in_issue[0]
                        self.total_counts[label] += 1
                        self.repo_counts[repo_name][label] += 1
                        domain = self.domain_mapping[repo_name]
                        self.domain_counts[domain][label] += 1
        except Exception as e:
            self.on_progress(f"Error processing {repo_name}: {str(e)}")

    def write_report(self):
        with open("report.md", "w") as f:
            # Title with SR name
            f.write(f"# {self.sr} findings breakdown\n\n")
            
            # Audits by domain
            f.write("## Audits by domain\n")
            f.write("| Domain | Number of Audits |\n")
            f.write("|--------|------------------|\n")
            audits_per_domain = defaultdict(int)
            for repo, domain in self.domain_mapping.items():
                audits_per_domain[domain] += 1
            
            total_audits = 0
            for domain in self.domains:
                if audits_per_domain[domain] > 0:
                    f.write(f"| {domain} | {audits_per_domain[domain]} |\n")
                    total_audits += audits_per_domain[domain]
            f.write(f"| **Total** | **{total_audits}** |\n\n")
            
            # Total findings
            f.write("## Total findings across all audits\n")
            f.write("| Severity | Count |\n")
            f.write("|----------|-------|\n")
            for label in SEVERITY_LABELS:
                if self.total_counts[label] > 0:
                    f.write(f"| {label} | {self.total_counts[label]} |\n")
            
            # Findings by domain
            f.write("\n## Findings by domain\n")
            for domain in self.domains:
                if any(self.domain_counts[domain].values()):
                    f.write(f"\n### {domain}\n")
                    f.write("| Severity | Count |\n")
                    f.write("|----------|-------|\n")
                    for label in SEVERITY_LABELS:
                        if self.domain_counts[domain][label] > 0:
                            f.write(f"| {label} | {self.domain_counts[domain][label]} |\n")
            
            # Findings by audit
            f.write("\n## Findings by audit\n")
            for domain in self.domains:
                domain_repos = [repo for repo, d in self.domain_mapping.items() if d == domain]
                if domain_repos:
                    f.write(f"\n### {domain}\n")
                    for repo_name in domain_repos:
                        if any(self.repo_counts[repo_name].values()):
                            f.write(f"\n#### {repo_name}\n")
                            f.write("| Severity | Count |\n")
                            f.write("|----------|-------|\n")
                            for label in SEVERITY_LABELS:
                                if self.repo_counts[repo_name][label] > 0:
                                    f.write(f"| {label} | {self.repo_counts[repo_name][label]} |\n")

    def analyze(self):
        self.is_running = True
        self.on_progress("Starting analysis...")
        
        # Reset counters
        self.total_counts.clear()
        self.repo_counts.clear()
        self.domain_mapping.clear()
        self.domain_counts.clear()
        
        github = Github(self.token)
        
        # Get repos for all domains
        all_repos = set()
        for domain in self.domains:
            if not self.is_running:
                return False
            repos = self.get_repos_for_domain(github, domain)
            all_repos.update(repos)
        
        self.on_progress(f"\nFound {len(all_repos)} repositories in total")
        
        # Process repositories
        for repo in all_repos:
            if not self.is_running:
                return False
            self.process_repository(github, repo)
        
        if self.is_running:
            self.write_report()
            self.on_progress("\nReport has been written to report.md")
            return True
        
        return False
    
    def stop(self):
        self.is_running = False
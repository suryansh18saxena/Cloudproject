from django.core.management.base import BaseCommand
from linux_labs.models import TerminalLab, TerminalChallenge


class Command(BaseCommand):
    help = 'Seed the 3 Linux Terminal Challenge Labs with questions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding Linux Terminal Labs...'))

        # ═══════════════════════════════════════════════════════════
        # LAB 1: System Rescue Mission (Beginner)
        # ═══════════════════════════════════════════════════════════
        lab1, _ = TerminalLab.objects.update_or_create(
            slug='system-rescue',
            defaults={
                'title': 'System Rescue Mission',
                'description': 'A Linux server has crashed and needs urgent recovery. Diagnose and fix system issues using the terminal.',
                'scenario': 'You are a junior sysadmin called in at midnight. The production server is down — services have crashed, disk is almost full, and processes are stuck. Your job is to bring it back online.',
                'difficulty': 'beginner',
                'duration_minutes': 25,
                'icon': 'healing',
                'order': 1,
            }
        )

        challenges_lab1 = [
            {
                'order': 1,
                'question_text': 'The application log shows errors. Which command would you use to find all ERROR lines in /var/log/app.log?',
                'option_a': 'grep "ERROR" /var/log/app.log',
                'option_b': 'find /var/log -name "ERROR"',
                'option_c': 'cat /var/log/app.log | sort',
                'option_d': 'ls -la /var/log/app.log',
                'correct_option': 'a',
                'expected_commands': ['grep.*ERROR.*/var/log/app\\.log'],
                'command_hint': 'Try using grep to search for patterns in log files.',
                'points': 10,
                'explanation': 'The grep command is used to search for text patterns in files. "grep ERROR /var/log/app.log" filters and displays only lines containing "ERROR".',
            },
            {
                'order': 2,
                'question_text': 'You need to check the disk usage to see which filesystem is almost full. Which command gives you a human-readable disk usage summary?',
                'option_a': 'du -sh /',
                'option_b': 'df -h',
                'option_c': 'ls -lh /',
                'option_d': 'free -h',
                'correct_option': 'b',
                'expected_commands': ['df\\s+-h'],
                'command_hint': 'df displays filesystem disk space usage, try it with the -h flag.',
                'points': 10,
                'explanation': 'df -h shows disk space usage in human-readable format (GB, MB). "du" shows directory sizes, "free" shows memory, and "ls" lists files.',
            },
            {
                'order': 3,
                'question_text': 'A zombie process is consuming resources. Which command shows all running processes with their status?',
                'option_a': 'top -n 1',
                'option_b': 'netstat -tlnp',
                'option_c': 'ps aux',
                'option_d': 'who -a',
                'correct_option': 'c',
                'expected_commands': ['ps\\s+aux'],
                'command_hint': 'Use ps with appropriate flags to list all processes with details.',
                'points': 10,
                'explanation': 'ps aux lists all processes with user, PID, CPU%, MEM%, and status. "Z" in the STAT column indicates zombie processes.',
            },
            {
                'order': 4,
                'question_text': 'You found that /tmp has large unnecessary files. Which command removes all files in /tmp older than 7 days?',
                'option_a': 'rm -rf /tmp/*',
                'option_b': 'find /tmp -type f -mtime +7 -delete',
                'option_c': 'del /tmp/*.old',
                'option_d': 'truncate -s 0 /tmp/*',
                'correct_option': 'b',
                'expected_commands': ['find\\s+/tmp.*-mtime.*-delete'],
                'command_hint': 'The find command with -mtime and -delete can remove files based on age.',
                'points': 10,
                'explanation': 'find /tmp -type f -mtime +7 -delete finds regular files in /tmp modified more than 7 days ago and deletes them safely.',
            },
            {
                'order': 5,
                'question_text': 'A critical config file /etc/nginx/nginx.conf has wrong permissions. What command sets it to be readable by owner only (600)?',
                'option_a': 'chown root:root /etc/nginx/nginx.conf',
                'option_b': 'chmod 777 /etc/nginx/nginx.conf',
                'option_c': 'chmod 600 /etc/nginx/nginx.conf',
                'option_d': 'setfacl -m u:root:rw /etc/nginx/nginx.conf',
                'correct_option': 'c',
                'expected_commands': ['chmod\\s+600\\s+/etc/nginx/nginx\\.conf'],
                'command_hint': 'chmod changes file permissions. 600 means read+write for owner only.',
                'points': 10,
                'explanation': 'chmod 600 sets permissions to rw------- allowing only the owner to read and write. This is crucial for sensitive config files.',
            },
        ]

        for ch in challenges_lab1:
            TerminalChallenge.objects.update_or_create(
                lab=lab1, order=ch['order'],
                defaults=ch
            )

        # ═══════════════════════════════════════════════════════════
        # LAB 2: Network Diagnostics (Intermediate)
        # ═══════════════════════════════════════════════════════════
        lab2, _ = TerminalLab.objects.update_or_create(
            slug='network-diagnostics',
            defaults={
                'title': 'Network Diagnostics',
                'description': 'A web application is unreachable. Diagnose network issues, fix DNS, firewall rules, and restore connectivity.',
                'scenario': 'The company website is down! Users report they cannot access the site. Your job is to systematically diagnose the network path and fix any issues you find.',
                'difficulty': 'intermediate',
                'duration_minutes': 30,
                'icon': 'lan',
                'order': 2,
            }
        )

        challenges_lab2 = [
            {
                'order': 1,
                'question_text': 'Users report the website is unreachable. What is the FIRST command you should run to check if the server can resolve the domain name?',
                'option_a': 'curl http://api.example.com',
                'option_b': 'nslookup api.example.com',
                'option_c': 'traceroute api.example.com',
                'option_d': 'ping -c 1 api.example.com',
                'correct_option': 'b',
                'expected_commands': ['nslookup\\s+api\\.example\\.com'],
                'command_hint': 'nslookup or dig can check DNS resolution for a domain.',
                'points': 10,
                'explanation': 'nslookup checks if DNS can resolve a domain to an IP. This is the first step because if DNS fails, nothing else will work.',
            },
            {
                'order': 2,
                'question_text': 'DNS resolution failed. Which file on Linux controls which DNS servers are used?',
                'option_a': '/etc/hosts',
                'option_b': '/etc/hostname',
                'option_c': '/etc/resolv.conf',
                'option_d': '/etc/network/interfaces',
                'correct_option': 'c',
                'expected_commands': ['cat\\s+/etc/resolv\\.conf'],
                'command_hint': 'Check the DNS configuration file to see the nameservers.',
                'points': 10,
                'explanation': '/etc/resolv.conf contains the DNS nameserver entries. If this file is empty or has wrong nameservers, DNS resolution fails.',
            },
            {
                'order': 3,
                'question_text': 'After fixing DNS, you need to check if the web server port (80) is actually open on the local machine. Which command checks listening ports?',
                'option_a': 'ifconfig eth0',
                'option_b': 'route -n',
                'option_c': 'netstat -tlnp',
                'option_d': 'arp -a',
                'correct_option': 'c',
                'expected_commands': ['netstat\\s+-tlnp'],
                'command_hint': 'netstat with the right flags shows which ports are listening.',
                'points': 10,
                'explanation': 'netstat -tlnp shows TCP listening ports with process names. -t=TCP, -l=listening, -n=numeric, -p=process info.',
            },
            {
                'order': 4,
                'question_text': 'You discover the firewall is blocking port 80. Which iptables command would add a rule to ACCEPT incoming traffic on port 80?',
                'option_a': 'iptables -A INPUT -p tcp --dport 80 -j ACCEPT',
                'option_b': 'iptables -D INPUT -p tcp --dport 80 -j DROP',
                'option_c': 'iptables -F',
                'option_d': 'iptables -L -n',
                'correct_option': 'a',
                'expected_commands': ['iptables.*-A.*INPUT.*--dport\\s+80.*-j\\s+ACCEPT'],
                'command_hint': 'Use iptables -A to append a rule allowing port 80 traffic.',
                'points': 10,
                'explanation': 'iptables -A INPUT -p tcp --dport 80 -j ACCEPT appends a rule to the INPUT chain allowing TCP traffic on port 80.',
            },
            {
                'order': 5,
                'question_text': 'Finally, which command would you use to verify the web server is responding correctly on port 80?',
                'option_a': 'wget --spider localhost:80',
                'option_b': 'ping localhost',
                'option_c': 'ssh localhost -p 80',
                'option_d': 'curl -I localhost:80',
                'correct_option': 'd',
                'expected_commands': ['curl.*(localhost|127\\.0\\.0\\.1)'],
                'command_hint': 'curl can make HTTP requests to test web server responses.',
                'points': 10,
                'explanation': 'curl -I localhost:80 sends a HEAD request and shows HTTP response headers, confirming the web server is responding. Option A also works but curl is more versatile.',
            },
        ]

        for ch in challenges_lab2:
            TerminalChallenge.objects.update_or_create(
                lab=lab2, order=ch['order'],
                defaults=ch
            )

        # ═══════════════════════════════════════════════════════════
        # LAB 3: Security Audit (Advanced)
        # ═══════════════════════════════════════════════════════════
        lab3, _ = TerminalLab.objects.update_or_create(
            slug='security-audit',
            defaults={
                'title': 'Security Audit',
                'description': 'Perform a security audit on a compromised server. Find backdoors, unauthorized users, and harden the system.',
                'scenario': 'A security breach was detected! Your CISO has tasked you to investigate a potentially compromised server. Find evidence of intrusion, identify malicious artifacts, and secure the system.',
                'difficulty': 'advanced',
                'duration_minutes': 35,
                'icon': 'shield',
                'order': 3,
            }
        )

        challenges_lab3 = [
            {
                'order': 1,
                'question_text': 'First, check for any unauthorized user accounts. Which command lists all users on the system with their shell?',
                'option_a': 'whoami',
                'option_b': 'cat /etc/passwd',
                'option_c': 'users',
                'option_d': 'id root',
                'correct_option': 'b',
                'expected_commands': ['cat\\s+/etc/passwd'],
                'command_hint': 'The /etc/passwd file contains all user accounts on the system.',
                'points': 10,
                'explanation': 'cat /etc/passwd shows all user accounts including their UID, GID, home directory, and login shell. Look for suspicious users with UID 0 or unexpected shells.',
            },
            {
                'order': 2,
                'question_text': 'You need to find hidden files that might be backdoors. Which command finds all hidden files (starting with .) in /tmp?',
                'option_a': 'ls /tmp',
                'option_b': 'find /tmp -name ".*" -type f',
                'option_c': 'du -sh /tmp',
                'option_d': 'stat /tmp',
                'correct_option': 'b',
                'expected_commands': ['find\\s+/tmp.*-name.*"?\\.\\*"?'],
                'command_hint': 'The find command with -name ".*" searches for hidden files.',
                'points': 10,
                'explanation': 'find /tmp -name ".*" -type f searches for hidden files (starting with a dot) in /tmp. Attackers often hide scripts as dot-files.',
            },
            {
                'order': 3,
                'question_text': 'You found a suspicious script at /tmp/.hidden_script.sh. How do you safely examine its contents WITHOUT executing it?',
                'option_a': 'bash /tmp/.hidden_script.sh',
                'option_b': 'source /tmp/.hidden_script.sh',
                'option_c': 'cat /tmp/.hidden_script.sh',
                'option_d': './/tmp/.hidden_script.sh',
                'correct_option': 'c',
                'expected_commands': ['cat\\s+/tmp/\\.hidden_script\\.sh'],
                'command_hint': 'Use cat to read the file contents without executing it.',
                'points': 10,
                'explanation': 'cat safely displays file contents. NEVER execute unknown scripts (bash, source, ./) as they could be malicious!',
            },
            {
                'order': 4,
                'question_text': 'The SSH log shows brute force attempts. Which command shows the last 20 lines of the application log to check for attack evidence?',
                'option_a': 'head -20 /var/log/app.log',
                'option_b': 'tail -20 /var/log/app.log',
                'option_c': 'more /var/log/app.log',
                'option_d': 'wc -l /var/log/app.log',
                'correct_option': 'b',
                'expected_commands': ['tail.*-20.*/var/log/app\\.log'],
                'command_hint': 'tail shows the last N lines of a file — useful for checking recent log entries.',
                'points': 10,
                'explanation': 'tail -20 /var/log/app.log shows the last 20 lines. Security logs often reveal attack patterns in the most recent entries.',
            },
            {
                'order': 5,
                'question_text': 'To prevent further SSH brute force attacks, you want to check which ports are currently open on the system. Which tool performs a local port scan?',
                'option_a': 'nmap localhost',
                'option_b': 'ping localhost',
                'option_c': 'traceroute localhost',
                'option_d': 'hostname -I',
                'correct_option': 'a',
                'expected_commands': ['nmap\\s+(localhost|127\\.0\\.0\\.1)'],
                'command_hint': 'nmap is a network scanner that shows open ports on a host.',
                'points': 10,
                'explanation': 'nmap localhost scans all ports on the local machine and reveals which services are exposed. This helps identify unauthorized services left by attackers.',
            },
        ]

        for ch in challenges_lab3:
            TerminalChallenge.objects.update_or_create(
                lab=lab3, order=ch['order'],
                defaults=ch
            )

        # ═══════════════════════════════════════════════════════════
        # LAB 4: Apache Web Server Deployment (Beginner)
        lab4, _ = TerminalLab.objects.update_or_create(
            slug='apache-deployment',
            defaults={
                'title': 'Apache Web Server Deployment',
                'description': 'Install, configure, and troubleshoot an Apache web server from scratch on Alpine Linux.',
                'scenario': 'A rogue script uninstalled the company web server! Your task in this Alpine Linux environment is to reinstall Apache, test its configuration, start the service, and verify it is serving traffic.',
                'difficulty': 'beginner',
                'duration_minutes': 20,
                'icon': 'language',
                'order': 4,
            }
        )

        challenges_lab4 = [
            {
                'order': 1,
                'question_text': 'The web server is missing! Which package manager command will install the Apache web server (the package is named "apache2")?',
                'option_a': 'apt-get install apache2',
                'option_b': 'yum install apache2',
                'option_c': 'apk add apache2',
                'option_d': 'pacman -S apache2',
                'correct_option': 'c',
                'expected_commands': ['apk\\s+add\\s+apache2'],
                'command_hint': 'This environment runs Alpine Linux, which uses the apk package manager.',
                'points': 10,
                'explanation': 'Alpine Linux uses the apk (Alpine Package Keeper) package manager. "apk add apache2" downloads and installs the Apache web server package.',
            },
            {
                'order': 2,
                'question_text': 'After installing Apache, you need to check if the main configuration file is present. Which file contains the main Apache configuration?',
                'option_a': '/etc/apache2/httpd.conf',
                'option_b': '/etc/nginx/nginx.conf',
                'option_c': '/etc/httpd/conf/httpd.conf',
                'option_d': '/var/www/html/index.php',
                'correct_option': 'a',
                'expected_commands': ['(ls|cat|vi|nano|stat).*\\s+/etc/apache2/httpd\\.conf'],
                'command_hint': 'On Alpine and Debian-based systems, Apache configurations are typically kept in /etc/apache2/',
                'points': 10,
                'explanation': 'On Alpine Linux, the main Apache configuration file is located at /etc/apache2/httpd.conf. Other distributions might use /etc/httpd/conf/httpd.conf.',
            },
            {
                'order': 3,
                'question_text': 'Before starting the server, how do you test the Apache configuration file for syntax errors?',
                'option_a': 'apachectl configtest',
                'option_b': 'httpd -t',
                'option_c': 'service apache2 status',
                'option_d': 'apache2 -syntax',
                'correct_option': 'b',
                'expected_commands': ['httpd\\s+-t'],
                'command_hint': 'The httpd daemon has a -t flag specifically for testing the syntax.',
                'points': 10,
                'explanation': 'The command "httpd -t" (or "apachectl configtest" on certain distros) checks the syntax of the Apache configuration files without starting the server, preventing startup crashes.',
            },
            {
                'order': 4,
                'question_text': 'The syntax looks good. Since Alpine Docker containers do not run systemd, which command directly starts the Apache daemon in the background?',
                'option_a': 'systemctl start apache2',
                'option_b': 'service apache2 start',
                'option_c': 'httpd -k start',
                'option_d': '/etc/init.d/apache2 start',
                'correct_option': 'c',
                'expected_commands': ['httpd\\s+-k\\s+start', 'httpd'],
                'command_hint': 'You can invoke the httpd executable directly to start it, often using the -k start option.',
                'points': 10,
                'explanation': '"httpd -k start" directly requests the daemon to start. Because our lightweight Alpine container lacks standard init systems like systemd, direct binary execution is required.',
            },
            {
                'order': 5,
                'question_text': 'The server is now running. Which tool can you use from the terminal to make a web request and verify it returns HTML content?',
                'option_a': 'ping localhost',
                'option_b': 'curl localhost',
                'option_c': 'netstat -tuln',
                'option_d': 'ssh localhost',
                'correct_option': 'b',
                'expected_commands': ['curl\\s+(localhost|127\\.0\\.0\\.1)'],
                'command_hint': 'curl is a command-line tool for transferring data with URLs.',
                'points': 10,
                'explanation': '"curl localhost" makes an HTTP GET request to the local web server and prints out the HTML response body, proving the server is up and responsive.',
            },
        ]

        for ch in challenges_lab4:
            TerminalChallenge.objects.update_or_create(
                lab=lab4, order=ch['order'],
                defaults=ch
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded 4 Linux Terminal Labs with 20 challenges!'))
        self.stdout.write(f'   Lab 1: {lab1.title} ({lab1.challenge_count} challenges)')
        self.stdout.write(f'   Lab 2: {lab2.title} ({lab2.challenge_count} challenges)')
        self.stdout.write(f'   Lab 3: {lab3.title} ({lab3.challenge_count} challenges)')
        self.stdout.write(f'   Lab 4: {lab4.title} ({lab4.challenge_count} challenges)')

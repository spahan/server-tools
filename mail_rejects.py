#!/usr/bin/python
import re
from datetime import datetime
from optparse import OptionParser

regexp = re.compile('(\w+\s+\d+\s+\d{2}:\d{2}:\d{2}) [^:]*: NOQUEUE: reject: RCPT from ([^[]*)\[([\.\d]*)]: (\d*)[\.\d\s]*<([^>]*)>: ([^;]*); from=<([^>]*)> to=<([^>]*)> proto=\S* helo=<([^>]*)>')
outformat = "% 30.30s\t% 20.20s\t% 20.20s\t% 20.20s\t%s"
header = outformat % ('FROM     ' , 'TO     ', 'HOST     ', 'HELO    ', 'code')
now = datetime.now()
year = now.year
now = datetime.strptime(now.strftime("%b %d %H:%M:%S"), "%b %d %H:%M:%S")

def parse_logfile():
    noqueue = list()
    with open('/var/log/mail.log') as f:
        for l in f:
            m = regexp.match(l)
            if m:
                r=list(m.groups())
                d=datetime.strptime(r[0], "%b %d %H:%M:%S")
                if d <= now:
                    r[0] = d.replace(year)
                else:
                    r[0] = d.replace(year-1)
                noqueue.append(r)
    return noqueue

def check_error(l,errno):
    def f(x):
        return x[4] == errno;
    return filter(f,l)

def check(l,g,s):
    def f(x):
        return x[g].find(s) == -1
    return filter(f,l)


def filter_code(l,c):
    def f(x):
        return x[3]!=c
    return filter(f,l)

def filter_date(l,min,max):
    def f(x):
        return x[0] >= min and x[0] <= max
    return filter(f,l)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-U", "--no-unknown-user", dest="user", help="do not report unknown user (550)", action="store_true", default=False)
    parser.add_option("-H", "--no-bad-helo", dest="helo", help="do not report bad helo strings (504)", action="store_true", default=False)
    parser.add_option("-v", "--verbose", dest="verbose", help="print out additional info", action="store_true", default=False)
    parser.add_option("-q", "--quiet", dest="output", help="only print summary", action="store_false", default=True)
    parser.add_option("-d", "--today", dest="today", help="only show messages from last 24 hours", action="store_true", default=False)
    (options, args) = parser.parse_args()

    a=parse_logfile()
    now=now.replace(year)

    if options.user:
        a = filter_code(a,'550')
    if options.helo:
        a = filter_code(a,'504')
    if options.today:
       a = filter_date(a, now.replace(day=now.day-1), now.replace(year+1))
    if options.output:
        i = 0;
        while i < len(a):
            if i % 50 == 0:
                print header
            if a[i][1]=='unknown':
                print outformat % (a[i][6][-30:], a[i][7][-20:], a[i][2][-20:], a[i][8][-20:], a[i][3])
            else:
                print outformat % (a[i][6][-30:], a[i][7][-20:], a[i][1][-20:], a[i][8][-20:], a[i][3])
            if options.verbose:
                print "%20s%s\t%.60s" % (' ', a[i][0], a[i][5][-60:])
            i += 1
        print header
    print "found %d noqueues" % len(a)   

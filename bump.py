import re

def hook(s, current_version, new_version):
    s = s.replace('<<>>', '')

    if (new_version.endswith('-dev')):
        pat = re.compile('## \[({})\]'.format(new_version))

        def dev_line(line):
            m = re.match(pat, line)
            if m:
                return m.group(1) == new_version

        lines = [line for line in s.splitlines() if not dev_line(line)]
        s = '\n'.join(lines)

    return s

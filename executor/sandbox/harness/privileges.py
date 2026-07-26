import os
import pwd

SOLUTION_ACCOUNT = "solution"


def confine_the_solution() -> None:
    account = pwd.getpwnam(SOLUTION_ACCOUNT)
    os.setgroups([])
    os.setresgid(account.pw_gid, account.pw_gid, account.pw_gid)
    os.setresuid(account.pw_uid, account.pw_uid, account.pw_uid)

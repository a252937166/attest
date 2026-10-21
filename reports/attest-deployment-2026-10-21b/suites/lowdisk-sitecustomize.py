# test harness only: every disk_usage call reports a volume with 1% free (a nearly full host)
import shutil, collections
_real = shutil.disk_usage
def _low(path):
    u = _real(path)
    return type(u)(u.total, u.total - u.total // 100, u.total // 100)
shutil.disk_usage = _low

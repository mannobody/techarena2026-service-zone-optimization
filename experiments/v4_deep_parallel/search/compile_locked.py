from pathlib import Path
import fcntl,subprocess,sys
R=Path(__file__).resolve().parent
with (R/'cpu_14.lock').open('w') as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 rc=subprocess.call(['taskset','-c','14,15','g++','-O3','-std=c++17',str(R/'src'/sys.argv[1]),'-o',str(R/'bin'/sys.argv[2])]);sys.exit(rc)

// base.h: заголовки std, время (elapsed), глобальные флаги отладки.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <climits>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iterator>
#include <memory>
#include <mutex>
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <unistd.h>
#include <fcntl.h>
#include <sched.h>
#include <malloc.h>
#include <csignal>
#include <vector>
#include <map>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;
using Clock = chrono::steady_clock;
static const Clock::time_point T0 = Clock::now();
static inline double elapsed() { return chrono::duration<double>(Clock::now() - T0).count(); }

static const double NEG = -1e300;
static bool DBG = false, DBG2 = false;

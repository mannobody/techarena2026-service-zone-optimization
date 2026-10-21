// output.h: вывод (запись одним write, сигналы), глобальное лучшее решение, пул элитных решений.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ========================================================== вывод (robust)
// Пред-сериализованный буфер + обработчик сигналов: даже убитый по таймеру
// процесс оставляет на диске валидный JSON.
static int g_fd = -1;
static string g_buf[2];
static atomic<int> g_idx{-1};
static atomic<bool> g_writing{false};

static size_t g_lastlen = 0;
static void raw_write(int which, bool sync) {
    if (g_fd < 0 || which < 0) return;
    const string& b = g_buf[which];
    if (lseek(g_fd, 0, SEEK_SET) < 0) return;
    size_t off = 0;
    while (off < b.size()) {
        ssize_t n = write(g_fd, b.data() + off, b.size() - off);
        if (n <= 0) break;
        off += n;
    }
    if (ftruncate(g_fd, off) != 0) { /* ignore */ }
    g_lastlen = off;
    if (sync) fsync(g_fd);
}
static void on_signal(int) {
    raw_write(g_idx.load(memory_order_acquire), true);
    _exit(0);
}
static mutex g_outmx;
static void publish(const string& text) {
    lock_guard<mutex> lk(g_outmx);
    int cur = g_idx.load(memory_order_relaxed);
    int nxt = cur == 0 ? 1 : 0;
    g_buf[nxt] = text;
    if (g_buf[nxt].size() < g_lastlen) g_buf[nxt].append(g_lastlen - g_buf[nxt].size(), ' ');
    g_idx.store(nxt, memory_order_release);
    raw_write(nxt, false);
}

static string serialize(const Inst& I, const vector<int>& asg, const vector<char>& isopen, const vector<int>& wof) {
    vector<vector<int>> mem(I.no);
    for (int s = 0; s < I.ns; s++) if (asg[s] >= 0) mem[asg[s]].push_back(s);
    string out = "[";
    bool first = true;
    char tmp[32];
    for (int o = 0; o < I.no; o++) {
        if (!isopen[o] || mem[o].empty()) continue;
        if (!first) out += ',';
        first = false;
        out += "{\"officeId\":";
        snprintf(tmp, sizeof tmp, "%d", o); out += tmp;
        out += ",\"sites\":[";
        sort(mem[o].begin(), mem[o].end());
        for (size_t i = 0; i < mem[o].size(); i++) {
            if (i) out += ',';
            snprintf(tmp, sizeof tmp, "%d", mem[o][i]); out += tmp;
        }
        out += "],\"workers\":[";
        bool fw = true;
        for (int w = 0; w < I.nw; w++) if (wof[w] == o) {
            if (!fw) out += ',';
            fw = false;
            snprintf(tmp, sizeof tmp, "%d", w); out += tmp;
        }
        out += "]}";
    }
    out += "]\n";
    return out;
}

// глобально лучшее
static mutex g_best_mx;
static atomic<double> g_best{0.0};
static vector<int> g_best_asg;
static vector<char> g_best_open;

struct Elite { double f; vector<int> asg; vector<char> open; };
static mutex g_el_mx;
static vector<Elite> g_elite;

static void push_elite(double f, const vector<int>& asg, const vector<char>& op) {
    lock_guard<mutex> lk(g_el_mx);
    for (auto& e : g_elite) if (fabs(e.f - f) <= 1e-9 * max(1.0, fabs(f))) return;
    g_elite.push_back({f, asg, op});
    sort(g_elite.begin(), g_elite.end(), [](const Elite& a, const Elite& b) { return a.f > b.f; });
    if (g_elite.size() > 6) g_elite.resize(6);
}
// выбрать элитное решение (с уклоном в лучшие); false, если пул пуст
static bool pick_elite(mt19937_64& rng, vector<int>& asg, vector<char>& op) {
    lock_guard<mutex> lk(g_el_mx);
    if (g_elite.empty()) return false;
    size_t i = 0;
    while (i + 1 < g_elite.size() && (rng() & 1)) i++;
    asg = g_elite[i].asg;
    op = g_elite[i].open;
    return true;
}

static bool offer(const Inst& I, Sol& s) {
    double f = s.objective();
    {
        lock_guard<mutex> lk(g_best_mx);
        if (f <= g_best.load(memory_order_relaxed) + 1e-9) return false;
    }
    vector<int> wof;
    if (!s.greedy_workers(&wof)) return false;
    double obj = 0;
    if (!verify(I, s.asg, s.isopen, wof, &obj)) return false;
    lock_guard<mutex> lk(g_best_mx);
    if (obj <= g_best.load(memory_order_relaxed) + 1e-9) return false;
    g_best.store(obj, memory_order_relaxed);
    g_best_asg = s.asg;
    g_best_open = s.isopen;
    publish(serialize(I, s.asg, s.isopen, wof));
    push_elite(obj, s.asg, s.isopen);
    if (DBG) {
        fprintf(stderr, "best t=%.2f obj=%.6f ops=", elapsed(), obj);
        for (int o = 0; o < I.no; o++) if (s.isopen[o]) fprintf(stderr, "%d,", o);
        fprintf(stderr, "\n");
    }
    return true;
}

// добавить решение в элиту, если оно близко к лучшему (с полной проверкой)
static void try_elite(const Inst& I, Sol& s) {
    double f = s.objective();
    double b = g_best.load(memory_order_relaxed);
    if (f <= 0 || f < b * (b > 0 ? 0.96 : 1.04)) return;
    vector<int> wof;
    double obj = 0;
    if (!s.greedy_workers(&wof)) return;
    if (!verify(I, s.asg, s.isopen, wof, &obj)) return;
    push_elite(obj, s.asg, s.isopen);
}

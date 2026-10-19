// lns.h: главный цикл LNS + отжиг, detect_cpus.
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

static void lns(Sol& s, mt19937_64& rng, double tend, double dp_deadline, bool deep,
                double lam_frac = 0.25, double ruin_scale = 1.0, bool lock_offices = false) {
    const Inst& I = *s.I;
    Engine E(s);
    E.rec = true;
    vector<int> cand;
    for (int x = 0; x < I.ns; x++) if (I.servable[x]) cand.push_back(x);
    if (cand.empty()) return;

    double scale = 0;
    {
        long cnt = 0;
        for (int o = 0; o < I.no; o++) if (s.isopen[o])
            for (int x = 0; x < I.ns; x += max(1, I.ns / 200)) { scale += fabs(I.pr(o, x)); cnt++; }
        scale = cnt ? scale / cnt : 1.0;
        if (!(scale > 0)) scale = 1.0;
    }
    Guide Gd(s, I.alpha * lam_frac);
    double cur = Gd.val();
    double T_hi = 0.25 * scale, T_lo = 1e-4 * scale, T = T_hi;
    double t_start = elapsed();
    // хвост чанка резервируем под детерминированную доводку
    double tloop = max(t_start + 0.05 * (tend - t_start), tend - min(0.3 * (tend - t_start), 25.0));
    // на больших инстансах один ход идёт десятки мс: не даём ему выйти за tend
    const double hardcap = I.ns > 1500 ? min(tloop + 1.0, tend) : 1e18;
    double dur = max(1e-3, tloop - t_start);
    uniform_real_distribution<double> U(0, 1);
    // при одном навыке на рабочего счётный критерий точен; иначе нужна проверка
    // назначением — один рабочий не может закрыть навыки в двух офисах сразу
    uint64_t wsig = ~0ULL;
    bool wok = false;
    auto feasible = [&]() {
        if (E.size_viol(-1, -1) > 0) return false;
        if (I.simple_workers) return true;
        if (s.sig != wsig) { wsig = s.sig; wok = s.greedy_workers(nullptr); }
        return wok;
    };
    vector<int> assigned;
    long it = 0, acc = 0, dpn = 0; long cnt[4][4] = {};  // [kind][0 try,1 fail,2 viol,3 acc]
    double tk[5] = {}, tk0 = 0; int lastk = -1;            // DBG: время по видам хода и DP
    // ALNS (по умолчанию вкл., ALNS=0 — фиксированные): вероятности видов хода по успеху на секунду (Ropke–Pisinger, нормировка по времени).
    // Виды: 0 план навыков, 1 сдвиг навыка, 2 переразрез, 3 одиночный, 4 ruin & recreate.
    static const bool alns = !getenv("ALNS") || atoi(getenv("ALNS")) > 0;
    static const int KLO[6] = {0, 7, 16, 45, 72, 100};
    double ap[5], asc[5] = {}, atm[5] = {}, arate[5] = {};
    for (int k = 0; k < 5; k++) ap[k] = (KLO[k + 1] - KLO[k]) / 100.0;
    int aop = -1;
    double at0 = elapsed(), aprev = 0, abest = -1e300, aseg = 0;
    bool arate_set = false;
    int since_dp = 0;
    vector<Pt> hh;

    auto try_dp = [&](void) {
        vector<int> sv = s.asg;
        vector<char> so = s.isopen;
        double before = s.objective();
        E.rec = false;
        double tdp = elapsed();
        bool ch = resize_dp(s, min(tloop + 5.0, dp_deadline), !lock_offices);
        if (ch) {
            repair_sizes(s);
            if (s.objective() < before - 1e-9) s.load_state(sv, so);
            else offer(I, s);
        }
        s.recompute_psum();
        if (greedy_fill(s, E, min(tloop + 2.0, dp_deadline))) { s.recompute_psum(); offer(I, s); }
        E.rec = true;
        E.jr.clear();
        s.recompute_psum();
        cur = Gd.val();
        dpn++;
        if (DBG) { tk[4] += elapsed() - tdp; tk0 += elapsed() - tdp; }
        if (alns) at0 += elapsed() - tdp;
        aprev = cur;
    };

    for (;; it++) {
        if ((it & 63) == 0 || I.ns > 1500) {  // большие: время на каждой итерации
            double now = elapsed();
            if (now >= tloop) break;
            T = T_hi * pow(T_lo / T_hi, (now - t_start) / dur);
            if ((it & 1023) == 0) Gd.dual_step(0.08);
            if ((it & 262143) == 0) { s.recompute_psum(); cur = Gd.val(); }
        }
        size_t mark = E.jr.size();
        int kind = rng() % 100;
        if (alns) {
            double t = elapsed();
            if (aop >= 0) {
                atm[aop] += t - at0;
                // за «принят хуже → снова лучше» почти не платим: иначе выигрывает раскачка отжига
                if (cur > aprev + 1e-12) asc[aop] += cur > abest + 1e-12 ? 33 : 3;
            } else aseg = t;
            abest = max(abest, cur);
            aprev = cur; at0 = t;
            // сегмент: обновить оценки «очков в секунду» и вероятности
            if (t - aseg > max(0.1, dur / 40)) {
                aseg = t;
                double sum = 0;
                for (int k = 0; k < 5; k++) {
                    if (atm[k] <= 0) continue;
                    double r = asc[k] / atm[k];
                    arate[k] = arate_set ? 0.7 * arate[k] + 0.3 * r : r;
                    asc[k] = atm[k] = 0;
                }
                arate_set = true;
                for (int k = 0; k < 5; k++) sum += arate[k];
                if (sum > 0) {
                    // половина — базовое распределение: один вид хода не вытесняет остальные
                    for (int k = 0; k < 5; k++)
                        ap[k] = 0.5 * (KLO[k + 1] - KLO[k]) / 100.0 + 0.5 * arate[k] / sum;
                }
            }
            double u = U(rng), c = 0;
            aop = 4;
            for (int k = 0; k < 5; k++) { c += ap[k]; if (u < c) { aop = k; break; } }
            kind = KLO[aop] + (int)(rng() % (KLO[aop + 1] - KLO[aop]));
        }
        if (DBG) { double t = elapsed(); if (lastk >= 0) tk[lastk] += t - tk0; tk0 = t;
                   lastk = kind < 16 ? 3 : kind < 45 ? 0 : kind < 72 ? 1 : 2; }

        if (kind < 7) {
            // --- пересчитать план навыков целиком
            cnt[3][0]++;
            if (!move_replan_skills(E, Gd, rng)) { cnt[3][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[3][2]++; E.undo(mark); continue; }
            {
                double f = Gd.val();
                double d = f - cur;
                if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                    cur = f; acc++; cnt[3][3]++; E.jr.clear();
                    if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                    if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
                } else E.undo(mark);
            }
            continue;
        }

        if (kind < 16) {
            // --- перераспределить навык между зонами
            cnt[3][0]++;
            if (!move_skill_shift(E, Gd, rng)) { cnt[3][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[3][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[3][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            } else E.undo(mark);
            continue;
        }

        if (kind < 45) {
            // --- переразрезать две зоны прямой
            cnt[0][0]++;
            if (!move_resplit(E, Gd, rng, U(rng) < 0.15, -1, -1, 9, hardcap)) { cnt[0][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[0][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[0][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
                if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            } else E.undo(mark);
            continue;
        }

        if (kind < 72) {
            // --- одиночный ход: перенести сайт в другой офис / снять
            int x = cand[rng() % cand.size()];
            int oold = s.asg[x];
            int onew;
            if (oold >= 0 && (rng() % 100) < 22) onew = -1;
            else {
                int tries = 0, pick = -1;
                for (int o : I.cand[x]) { if (s.isopen[o]) { if (tries == 0 || (rng() % 4) == 0) pick = o; if (++tries >= 5) break; } }
                onew = pick;
            }
            cnt[1][0]++;
            if (onew == oold || (oold < 0 && onew < 0)) { cnt[1][1]++; continue; }
            if (oold >= 0) E.doRemove(x);
            if (onew >= 0 && !E.doAdd(x, onew)) { cnt[1][1]++; E.undo(mark); continue; }
            if (!feasible()) { cnt[1][2]++; E.undo(mark); continue; }
            double f = Gd.val();
            double d = f - cur;
            if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
                cur = f; acc++; cnt[1][3]++; E.jr.clear();
                if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
            } else E.undo(mark);
            if (++since_dp > 20000 && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
            continue;
        }

        // --- ruin & recreate
        assigned.clear();
        for (int x = 0; x < I.ns; x++) if (s.asg[x] >= 0) assigned.push_back(x);
        int mode = rng() % 100;
        static const bool xover = !getenv("XOVER") || atoi(getenv("XOVER")) > 0;  // XOVER=0 — выключить
        if (xover && mode < 12 && !lock_offices) {
            if (!ruin_crossover(E, rng)) { E.undo(mark); continue; }
            mode = -1;
        }
        s.begin_defer();
        if (mode < 0) {
        } else if (mode < 40 && !assigned.empty()) {
            int c = assigned[rng() % assigned.size()];
            int q = max(1, (int)((3 + rng() % 25) * ruin_scale));
            vector<pair<double, int>> v;
            v.reserve(assigned.size());
            for (int x : assigned) {
                double dx = I.P[x].x - I.P[c].x, dy = I.P[x].y - I.P[c].y;
                v.push_back({dx * dx + dy * dy, x});
            }
            if ((int)v.size() > q) nth_element(v.begin(), v.begin() + q, v.end());
            for (int i = 0; i < min((int)v.size(), q); i++) E.doRemove(v[i].second);
        } else if (mode < 62 && !assigned.empty()) {
            int q = max(1, (int)((3 + rng() % 20) * ruin_scale));
            shuffle(assigned.begin(), assigned.end(), rng);
            for (int i = 0; i < min((int)assigned.size(), q); i++) E.doRemove(assigned[i]);
        } else if (mode < 80) {
            vector<int> op;
            for (int o = 0; o < I.no; o++) if (s.isopen[o] && s.size_[o] > 0) op.push_back(o);
            if (op.empty()) { E.undo(mark); continue; }
            int o = op[rng() % op.size()];
            vector<int> mem = s.members[o];
            shuffle(mem.begin(), mem.end(), rng);
            int q = max(1, (int)(mem.size() * (0.2 + 0.6 * U(rng))));
            for (int i = 0; i < min((int)mem.size(), q); i++) E.doRemove(mem[i]);
        } else if (mode < 91) {
            if (lock_offices) { E.undo(mark); continue; }
            vector<int> op;
            for (int o = 0; o < I.no; o++) if (s.isopen[o]) op.push_back(o);
            if (op.empty()) { E.undo(mark); continue; }
            E.doClose(op[rng() % op.size()]);
        } else {
            vector<int> cl;
            for (int o = 0; o < I.no; o++) if (!s.isopen[o]) cl.push_back(o);
            if (cl.empty()) { E.undo(mark); continue; }
            int o = cl[rng() % cl.size()];
            const Pt& q = I.P[I.ns + o];
            // OSWAP=1: обмен офисов за один ход — заодно закрыть ближайший открытый,
            // иначе переход между наборами одного размера идёт через худший набор
            static const bool oswap = getenv("OSWAP") && atoi(getenv("OSWAP")) > 0;
            if (oswap && !lock_offices && (rng() & 1)) {
                int oc = -1;
                double bd = 1e300;
                for (int p = 0; p < I.no; p++) if (s.isopen[p]) {
                    double dx = I.P[I.ns + p].x - q.x, dy = I.P[I.ns + p].y - q.y;
                    if (dx * dx + dy * dy < bd) { bd = dx * dx + dy * dy; oc = p; }
                }
                if (oc >= 0) {
                    E.doClose(oc);
                    assigned.clear();
                    for (int x = 0; x < I.ns; x++) if (s.asg[x] >= 0) assigned.push_back(x);
                }
            }
            vector<pair<double, int>> v;
            v.reserve(assigned.size());
            for (int x : assigned) {
                double dx = I.P[x].x - q.x, dy = I.P[x].y - q.y;
                v.push_back({dx * dx + dy * dy, x});
            }
            int k = min((int)v.size(), 10 + (int)(rng() % 40));
            if ((int)v.size() > k) nth_element(v.begin(), v.begin() + k, v.end());
            for (int i = 0; i < k; i++) E.doRemove(v[i].second);
            s.end_defer();
            E.doOpen(o);
        }
        s.end_defer();
        cnt[2][0]++;
        recreate(E, Gd, rng, U(rng) < 0.3, 5, hardcap);
        if (!feasible()) { cnt[2][2]++; E.undo(mark); continue; }
        double f = Gd.val();
        double d = f - cur;
        if (d > -1e-12 || U(rng) < exp(d / max(1e-12, T))) {
            cur = f; acc++; cnt[2][3]++; E.jr.clear();
            if (s.objective_fast() > g_best.load(memory_order_relaxed) + 1e-9) { offer(I, s); since_dp = 100000; }
            if (++since_dp > (deep ? 120 : 300) && elapsed() < dp_deadline) { since_dp = 0; try_dp(); }
        } else E.undo(mark);
    }
    if (elapsed() < dp_deadline) try_dp();
    offer(I, s);
    polish(s, rng, min(tend, dp_deadline), dp_deadline, lock_offices);
    try_elite(I, s);
    if (DBG)
        fprintf(stderr, "   lns it=%ld acc=%ld dp=%ld obj=%.4f best=%.4f | split %ld/%ld/%ld/%ld  single %ld/%ld/%ld/%ld  ruin %ld/%ld/%ld/%ld  skill %ld/%ld/%ld/%ld\n",
                it, acc, dpn, s.objective(), g_best.load(),
                cnt[0][0],cnt[0][1],cnt[0][2],cnt[0][3], cnt[1][0],cnt[1][1],cnt[1][2],cnt[1][3], cnt[2][0],cnt[2][1],cnt[2][2],cnt[2][3], cnt[3][0],cnt[3][1],cnt[3][2],cnt[3][3]);
    if (DBG)
        fprintf(stderr, "   time split %.2f single %.2f ruin %.2f skill %.2f dp %.2f | alns p %.2f %.2f %.2f %.2f %.2f\n",
                tk[0], tk[1], tk[2], tk[3], tk[4], ap[0], ap[1], ap[2], ap[3], ap[4]);
}

// Сколько потоков запускать: ядра, доступные процессу (sched_getaffinity — системный
// вызов, учитывает --cpuset-cpus). Файлы (/sys, /proc, квоту cgroup) не читаем: по
// правилам открывать можно только instance.json и solution.json.
static int detect_cpus() {
    if (getenv("NT")) return max(1, atoi(getenv("NT")));
    cpu_set_t cs;
    CPU_ZERO(&cs);
    int n = sched_getaffinity(0, sizeof cs, &cs) == 0 ? CPU_COUNT(&cs) : 1;
    if (n < 1) n = 1;
    if (n > 16) n = 16;
    if (n > 2) {
        // квоту (docker --cpus) affinity не видит: меряем, сколько потоков реально идут
        // параллельно — суммарное процессорное время n крутящихся потоков за ~0.3 с
        atomic<bool> stop{false};
        vector<double> cpu(n, 0.0);
        vector<thread> th;
        for (int i = 0; i < n; i++)
            th.emplace_back([&stop, &cpu, i] {
                volatile double x = 0;
                while (!stop.load(memory_order_relaxed)) for (int j = 0; j < 20000; j++) x = x + j;
                timespec ts;
                clock_gettime(CLOCK_THREAD_CPUTIME_ID, &ts);
                cpu[i] = ts.tv_sec + ts.tv_nsec * 1e-9;
            });
        double t0 = elapsed();
        while (elapsed() - t0 < 0.3) usleep(10000);
        stop = true;
        for (auto& t : th) t.join();
        double wall = max(1e-3, elapsed() - t0), sum = 0;
        for (double c : cpu) sum += c;
        int eff = (int)floor(sum / wall + 0.5);
        if (DBG) fprintf(stderr, "cpus: affinity %d, measured %.2f\n", n, sum / wall);
        n = max(1, min(n, eff));
    }
    return n;
}

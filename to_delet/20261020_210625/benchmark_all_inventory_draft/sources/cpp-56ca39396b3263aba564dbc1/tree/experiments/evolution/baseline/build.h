// build.h: конструкторы стартовых разбиений (power diagram, секторы, гильотина, ...).
// Часть solve.cpp (одна единица трансляции): включается только из него, порядок важен.

// ================================================================ сборка
// Кому из офисов достаётся дефицитный навык: берём N_k зон с наибольшей
// прибылью от сайтов, которым этот навык нужен. Пара итераций с учётом того,
// что сайту нужны ВСЕ его навыки.
static void plan_skills(const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                        vector<char>& allow, mt19937_64* rng = nullptr, double temp = 0.0) {
    int K = ops.size();
    vector<int> idx(I.no, -1);
    for (int b = 0; b < K; b++) idx[ops[b]] = b;
    allow.assign((size_t)K * I.nsk, 1);
    vector<char> ok(I.ns, 0);
    for (int x = 0; x < I.ns; x++)
        ok[x] = I.servable[x] && cellOf[x] >= 0 && idx[cellOf[x]] >= 0 && I.pr(cellOf[x], x) > 0;
    for (int iter = 0; iter < 3; iter++) {
        vector<char> prev = allow;
        fill(allow.begin(), allow.end(), 1);
        for (int k = 0; k < I.nsk; k++) {
            if (I.Nk[k] >= K) continue;
            vector<double> val(K, 0.0);
            for (int x = 0; x < I.ns; x++) {
                if (!ok[x]) continue;
                if (!binary_search(I.skillset[x].begin(), I.skillset[x].end(), k)) continue;
                val[idx[cellOf[x]]] += I.pr(cellOf[x], x);
            }
            vector<int> ord(K);
            iota(ord.begin(), ord.end(), 0);
            if (rng && temp > 0) {
                // случайный выбор зон с весом по прибыли: распределение навыков —
                // отдельное измерение поиска, жадный выбор застревает в одном варианте
                vector<double> w(K);
                double mx = *max_element(val.begin(), val.end());
                double sc = max(1e-12, fabs(mx)) * temp;
                for (int b = 0; b < K; b++) w[b] = exp((val[b] - mx) / sc);
                vector<int> pick;
                for (int r = 0; r < K; r++) {
                    double tot = 0;
                    for (int b = 0; b < K; b++) tot += w[b];
                    if (tot <= 0) break;
                    double u = (double)((*rng)() % 1000000) / 1000000.0 * tot, acc2 = 0;
                    int sel = -1;
                    for (int b = 0; b < K; b++) { acc2 += w[b]; if (acc2 >= u) { sel = b; break; } }
                    if (sel < 0) break;
                    pick.push_back(sel);
                    w[sel] = 0;
                }
                for (int b = 0; b < K; b++) if (find(pick.begin(), pick.end(), b) == pick.end()) pick.push_back(b);
                ord = pick;
            } else
                stable_sort(ord.begin(), ord.end(), [&](int a, int b) { return val[a] > val[b]; });
            for (int r = I.Nk[k]; r < K; r++) allow[(size_t)ord[r] * I.nsk + k] = 0;
        }
        for (int x = 0; x < I.ns; x++) {
            if (!I.servable[x] || cellOf[x] < 0 || idx[cellOf[x]] < 0 || I.pr(cellOf[x], x) <= 0) { ok[x] = 0; continue; }
            ok[x] = 1;
            for (int k : I.skillset[x]) if (!allow[(size_t)idx[cellOf[x]] * I.nsk + k]) { ok[x] = 0; break; }
        }
        if (allow == prev) break;
    }
}

// Ценность плана навыков: суммарная прибыль сайтов, которые при нём обслужимы.
static double plan_value(const Inst& I, const vector<int>& cellOf, const vector<int>& idx,
                         const vector<char>& allow) {
    double v = 0;
    for (int x = 0; x < I.ns; x++) {
        int o = cellOf[x];
        if (o < 0 || idx[o] < 0 || !I.servable[x]) continue;
        double p = I.pr(o, x);
        if (p <= 0) continue;
        bool ok = true;
        for (int k : I.skillset[x])
            if (!allow[(size_t)idx[o] * I.nsk + k]) { ok = false; break; }
        if (ok) v += p;
    }
    return v;
}

// Локальный поиск по матрице allow[зона][навык]: добавить дефицитный навык
// свободной зоне или перенести его между зонами. Один жадный проход, как было
// раньше, сильно недобирает: офисы остаются без навыков и простаивают.
static void optimize_skill_plan(const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                                vector<char>& allow, double deadline) {
    int K = ops.size();
    if (!K) return;
    vector<int> idx(I.no, -1);
    for (int b = 0; b < K; b++) idx[ops[b]] = b;
    vector<int> scarce;
    for (int k = 0; k < I.nsk; k++) if (I.Nk[k] > 0 && I.Nk[k] < K) scarce.push_back(k);
    if (scarce.empty()) return;
    long long work = (long long)I.ns * scarce.size() * (K + K * K);
    int rounds = work > 200000000LL ? 1 : (work > 40000000LL ? 3 : 8);
    double best = plan_value(I, cellOf, idx, allow);
    for (int r = 0; r < rounds; r++) {
        bool imp = false;
        for (int k : scarce) {
            if (elapsed() > deadline) return;
            int cnt = 0;
            for (int b = 0; b < K; b++) cnt += allow[(size_t)b * I.nsk + k] ? 1 : 0;
            if (cnt < I.Nk[k]) {                       // есть свободный рабочий — кому отдать
                for (int b = 0; b < K; b++) {
                    if (allow[(size_t)b * I.nsk + k]) continue;
                    allow[(size_t)b * I.nsk + k] = 1;
                    double v = plan_value(I, cellOf, idx, allow);
                    if (v > best + 1e-9) { best = v; imp = true; cnt++; }
                    else allow[(size_t)b * I.nsk + k] = 0;
                }
            }
            for (int a = 0; a < K; a++) {              // перенести навык между зонами
                if (!allow[(size_t)a * I.nsk + k]) continue;
                for (int b = 0; b < K; b++) {
                    if (b == a || allow[(size_t)b * I.nsk + k]) continue;
                    allow[(size_t)a * I.nsk + k] = 0;
                    allow[(size_t)b * I.nsk + k] = 1;
                    double v = plan_value(I, cellOf, idx, allow);
                    if (v > best + 1e-9) { best = v; imp = true; a = b; }
                    else { allow[(size_t)a * I.nsk + k] = 1; allow[(size_t)b * I.nsk + k] = 0; }
                }
            }
        }
        if (!imp) break;
    }
}

static void realize(Sol& s, const Inst& I, const vector<int>& ops, const vector<int>& cellOf,
                    double deadline = 1e18, mt19937_64* rng = nullptr, double temp = 0.0) {
    s.init(I);
    for (int o : ops) {
        if (s.cov[I.ns + o] > 0) continue;
        s.isopen[o] = 1;
        s.rebuild_hull(o);
    }
    Engine E(s);
    vector<char> allow;
    plan_skills(I, ops, cellOf, allow, rng, temp);
    if (temp <= 0) optimize_skill_plan(I, ops, cellOf, allow, deadline);
    for (size_t b = 0; b < ops.size(); b++)
        for (int k = 0; k < I.nsk; k++)
            if (!allow[b * I.nsk + k]) E.set_ban(ops[b], k, true);
    vector<pair<double, pair<int, int>>> order;
    order.reserve(I.ns);
    for (int x = 0; x < I.ns; x++) {
        int o = cellOf[x];
        if (o < 0 || !s.isopen[o] || !I.servable[x]) continue;
        order.push_back({I.pr(o, x), {x, o}});
    }
    sort(order.rbegin(), order.rend());
    // План навыков считает по числу рабочих N_k, а многопрофильный рабочий не
    // закроет навыки в двух офисах сразу: сайт с новым для офиса навыком берём,
    // только если рабочих ещё можно раздать (WFIX=0 — без проверки)
    static const bool wfix = !getenv("WFIX") || atoi(getenv("WFIX")) > 0;
    const bool chk = wfix && !I.simple_workers;
    auto add = [&](int x, int o) {
        uint64_t sg = s.sig;
        if (E.doAdd(x, o) && chk && s.sig != sg && !s.greedy_workers(nullptr)) s.remove_site(x);
    };
    size_t i = 0;
    for (auto& e : order) {
        if ((++i & 63) == 0 && elapsed() > deadline) break;
        add(e.second.first, e.second.second);
    }
    E.clear_ban();
    // вторым проходом добиваем то, что влезает и без плана
    i = 0;
    for (auto& e : order) {
        if ((++i & 63) == 0 && elapsed() > deadline) break;
        if (s.asg[e.second.first] < 0) add(e.second.first, e.second.second);
    }
}

// конструктор: ближайший по дороге открытый офис
static vector<int> ctor_road(const Inst& I, const vector<int>& ops) {
    vector<int> c(I.ns, -1);
    for (int s = 0; s < I.ns; s++) {
        int b = -1;
        for (int o : ops) if (b < 0 || I.d(o, s) < I.d(b, s)) b = o;
        c[s] = b;
    }
    return c;
}
// конструктор: угловые секторы вокруг центра (выпуклые клинья)
static vector<int> ctor_sector(const Inst& I, const vector<int>& ops, Pt cen) {
    int K = ops.size();
    vector<pair<double, int>> ang;
    for (int o : ops) ang.push_back({atan2(I.P[I.ns + o].y - cen.y, I.P[I.ns + o].x - cen.x), o});
    sort(ang.begin(), ang.end());
    vector<double> bnd(K);
    for (int i = 0; i < K; i++) {
        double a = ang[i].first, b = ang[(i + 1) % K].first;
        if (b < a) b += 2 * M_PI;
        bnd[i] = 0.5 * (a + b);
    }
    vector<int> c(I.ns, -1);
    for (int s = 0; s < I.ns; s++) {
        double a = atan2(I.P[s].y - cen.y, I.P[s].x - cen.x);
        int pick = ang[0].second;
        for (int i = 0; i < K; i++) {
            double lo = i == 0 ? bnd[K - 1] - 2 * M_PI : bnd[i - 1];
            double hi = bnd[i];
            double aa = a;
            if (aa < lo) aa += 2 * M_PI;
            if (aa >= lo && aa < hi) { pick = ang[i].second; break; }
        }
        c[s] = pick;
    }
    return c;
}

// Конструктор «гильотина»: рекурсивно делим множество офисов прямой, выбирая
// направление и положение разреза по честной сумме max(reward - dist, 0).
// В отличие от power diagram опирается на дорожные расстояния, а не на
// геометрическую близость — важно там, где они расходятся.
static void guillotine_rec(const Inst& I, vector<int> ops, vector<int> sites,
                           vector<int>& cellOf, mt19937_64& rng, int ndir) {
    if (ops.empty()) return;
    if (ops.size() == 1) { for (int x : sites) cellOf[x] = ops[0]; return; }
    int K = ops.size();
    double bestv = NEG, bdx = 1, bdy = 0, bcut = 0;
    int bm = 1;
    vector<int> bord;
    vector<double> lv(sites.size()), rv(sites.size());
    vector<pair<double, int>> sp(sites.size());
    for (int di = 0; di < ndir; di++) {
        double th = di < ndir / 2 ? M_PI * di / max(1, ndir / 2)
                                  : 2 * M_PI * (double)(rng() % 10000) / 10000.0;
        double dx = cos(th), dy = sin(th);
        vector<pair<double, int>> op2;
        for (int o : ops) op2.push_back({I.P[I.ns + o].x * dx + I.P[I.ns + o].y * dy, o});
        sort(op2.begin(), op2.end());
        for (size_t i = 0; i < sites.size(); i++)
            sp[i] = {I.P[sites[i]].x * dx + I.P[sites[i]].y * dy, sites[i]};
        sort(sp.begin(), sp.end());
        for (int m = 1; m < K; m++) {
            double lo = op2[m - 1].first, hi = op2[m].first;
            if (hi - lo < 1e-12 * max(1.0, I.ext)) continue;
            for (size_t i = 0; i < sp.size(); i++) {
                int x = sp[i].second;
                double a = NEG, b = NEG;
                for (int j = 0; j < m; j++) a = max(a, I.pr(op2[j].second, x));
                for (int j = m; j < K; j++) b = max(b, I.pr(op2[j].second, x));
                lv[i] = max(0.0, a); rv[i] = max(0.0, b);
            }
            double cur = 0;
            for (size_t i = 0; i < sp.size(); i++) cur += rv[i];   // разрез на уровне lo
            double bc = lo, bv = NEG;
            for (size_t i = 0;; i++) {
                if (cur > bv) { bv = cur; bc = i == 0 ? lo : sp[i - 1].first; }
                if (i >= sp.size() || sp[i].first > hi) break;
                if (sp[i].first <= lo) { cur += lv[i] - rv[i]; continue; }
                cur += lv[i] - rv[i];
            }
            if (bv > bestv) {
                bestv = bv; bdx = dx; bdy = dy; bcut = bc; bm = m;
                bord.clear();
                for (auto& e : op2) bord.push_back(e.second);
            }
        }
    }
    if (bestv <= NEG / 2) { for (int x : sites) cellOf[x] = ops[0]; return; }
    vector<int> lo_ops(bord.begin(), bord.begin() + bm), hi_ops(bord.begin() + bm, bord.end());
    vector<int> lo_s, hi_s;
    for (int x : sites)
        (I.P[x].x * bdx + I.P[x].y * bdy <= bcut ? lo_s : hi_s).push_back(x);
    guillotine_rec(I, lo_ops, lo_s, cellOf, rng, ndir);
    guillotine_rec(I, hi_ops, hi_s, cellOf, rng, ndir);
}

static vector<int> ctor_guillotine(const Inst& I, const vector<int>& ops, mt19937_64& rng) {
    vector<int> cellOf(I.ns, -1), all(I.ns);
    iota(all.begin(), all.end(), 0);
    guillotine_rec(I, ops, all, cellOf, rng, I.ns > 2000 ? 8 : 16);
    return cellOf;
}

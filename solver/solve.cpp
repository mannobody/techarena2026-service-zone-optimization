// TechArena 2026, кейс 3 "Service Zone Optimization" — решатель на C++.
// Только стандартная библиотека (+ pthread). Код разбит на части solver/*.h,
// solve.cpp включает их по порядку (одна единица трансляции). Для посылки
// submission/make_zips.sh склеивает всё обратно в один solve.cpp.
//
// Читает instance.json, пишет solution.json в текущем каталоге.
// Отладка: ./solve [in.json] [out.json] [секунды] ; лимит также через TL=...,
// потоки NT=..., зерно SEED=... (без SEED поведение как раньше).
//
// Схема:
//   1) конструкторы стартовых разбиений (power diagram, секторы, дорожная близость,
//      разрезы прямыми) — все дают геометрически допустимое разбиение;
//   2) точный DP "какие сайты оставить" при фиксированных зонах: окно нагрузки
//      [lo,hi] + 0/1-рюкзак по числу задач. Удаление сайтов не ломает геометрию,
//      поэтому DP точен внутри зон;
//   3) LNS (ruin & recreate) + отжиг по одиночным ходам, многопоточно;
//   4) защита от TLE: пред-сериализованный буфер + обработчик сигналов.

#include "base.h"
#include "json.h"
#include "geom.h"
#include "inst.h"
#include "sol.h"
#include "check.h"
#include "output.h"
#include "dp.h"
#include "fast.h"
#include "engine.h"
#include "build.h"
#include "moves.h"
#include "improve.h"
#include "lns.h"
#include "exact2.h"

// ================================================================== main
struct Cand { double f; vector<int> op; vector<double> h; vector<Pt> G; };

static void worker(const Inst& I, const Fast& F, const vector<Cand>& cands,
                   uint64_t seed, double tend, double dp_deadline, int tid) {
    static const double LAMS[4] = {0.25, 0.10, 0.50, 0.0};
    static const double RUINS[3] = {1.0, 0.4, 2.5};
    const double PA = 0.25 * tend, P3 = 0.85 * tend;
    mt19937_64 rng(seed);
    Sol s;
    uniform_real_distribution<double> U(0, 1);
    Pt cen{0, 0};
    for (int o = 0; o < I.no; o++) { cen.x += I.P[I.ns + o].x; cen.y += I.P[I.ns + o].y; }
    if (I.no) { cen.x /= I.no; cen.y /= I.no; }
    const int NC = 6;
    if (cands.empty()) return;

    // строит стартовое решение по связке (набор офисов, конструктор)
    auto build = [&](int ci, int ctor, double deadline, bool refine, double skt = 0.0) {
        const Cand& c = cands[ci];
        vector<double> h = c.h;
        vector<Pt> G = c.G;
        if (h.empty()) { h.assign(I.no, 0.0); G.assign(I.P.begin() + I.ns, I.P.end()); }
        vector<int> cellOf(I.ns, -1);
        if (ctor <= 1) {
            if (refine) F.search(c.op, h, G, 300, min(deadline, elapsed() + 3.0));
            if (ctor == 0) {
                vector<vector<int>> mem;
                if (F.evaluate(c.op, h, G, &mem) > NEG / 2 && !mem.empty())
                    for (int o : c.op) for (int x : mem[o]) cellOf[x] = o;
            } else {
                vector<int> cell;
                F.cells(c.op, h, G, cell);
                for (int x = 0; x < I.ns; x++) cellOf[x] = c.op[cell[x]];
            }
        } else if (ctor == 2) cellOf = ctor_road(I, c.op);
        else if (ctor == 3) cellOf = ctor_sector(I, c.op, cen);
        else if (ctor == 5) cellOf = ctor_guillotine(I, c.op, rng);
        else {
            Pt r{cen.x + (U(rng) - 0.5) * 2 * I.ext, cen.y + (U(rng) - 0.5) * 2 * I.ext};
            cellOf = ctor_sector(I, c.op, r);
        }
        realize(s, I, c.op, cellOf, deadline, &rng, skt);
        repair_sizes(s);
        Engine E(s);
        if (elapsed() < dp_deadline) { resize_dp(s, dp_deadline); repair_sizes(s); }
        s.recompute_psum();
        greedy_fill(s, E, min(deadline, dp_deadline));
        s.recompute_psum();
        offer(I, s);
    };

    // --- фаза A: дешёвый отбор всех связок
    int NCOMBO = (int)cands.size() * NC;
    vector<pair<double, int>> rank;
    for (int t = 0; t < NCOMBO && elapsed() < PA; t++) {
        int combo = (t + tid * 7) % NCOMBO;
        build(combo % cands.size(), combo / cands.size(), min(PA, dp_deadline), false);
        rank.push_back({s.objective(), combo});
    }
    // Ранжируем НАБОРЫ ОФИСОВ, а не связки: набор с большим числом офисов
    // стартует хуже (навыки и геометрию ещё надо развести), но после глубокого
    // поиска часто выигрывает. Берём для каждого набора его лучший конструктор.
    {
        vector<pair<double, int>> bestOf(cands.size(), {NEG, 0});
        for (auto& e : rank) {
            int ci = e.second % (int)cands.size();
            if (e.first > bestOf[ci].first) bestOf[ci] = {e.first, e.second};
        }
        rank.clear();
        for (size_t ci = 0; ci < cands.size(); ci++)
            if (bestOf[ci].first > NEG / 2) rank.push_back(bestOf[ci]);
        sort(rank.rbegin(), rank.rend());
    }
    if (rank.empty()) rank.push_back({0.0, tid % NCOMBO});
    if (DBG && tid == 0) {
        for (size_t i = 0; i < cands.size(); i++) {
            fprintf(stderr, "cand%zu f=%.2f ops=", i, cands[i].f);
            for (int o : cands[i].op) fprintf(stderr, "%d,", o);
            fprintf(stderr, "\n");
        }
        for (size_t i = 0; i < rank.size() && i < 8; i++)
            fprintf(stderr, "  rank%zu val=%.2f cand=%d ctor=%d\n", i, rank[i].first,
                    rank[i].second % (int)cands.size(), rank[i].second / (int)cands.size());
    }

    // --- фаза B и C: глубокие прогоны по лучшим связкам и по общему лучшему
    int round = 0;
    while (elapsed() < tend - max(0.5, 0.02 * tend)) {
        double now0 = elapsed();
        double left = tend - now0;
        bool last = now0 >= P3;
        double chunk = last ? left : max(1.5, min(left, min(0.12 * tend, left / 2.0)));
        double ce = now0 + chunk;
        bool fromBest = false;
        // половина потоков идёт независимо, чтобы выборка была разнообразнее
        double pBest = last ? 1.0 : ((tid & 1) ? 0.0 : 0.5);
        if (U(rng) < pBest) {
            vector<int> ea;
            vector<char> eo;
            bool got = last ? false : pick_elite(rng, ea, eo);
            if (!got) {
                lock_guard<mutex> lk(g_best_mx);
                ea = g_best_asg;
                eo = g_best_open;
                got = !ea.empty();
            }
            if (got) { s.init(I); s.load_state(ea, eo); fromBest = true; }
        }
        if (!fromBest) {
            int r = round % max<size_t>(1, min<size_t>(rank.size(), 6));
            int combo = rank[r].second;
            // каждый третий глубокий прогон стартует со случайного плана навыков
            double skt = (round % 3 == 2) ? 0.15 + 0.5 * U(rng) : 0.0;
            build(combo % cands.size(), combo / cands.size(), min(ce, dp_deadline), true, skt);
        }
        round++;
        if (!fromBest && !last) {
            // сначала заставляем выбранный набор офисов заработать, потом отпускаем
            lns(s, rng, now0 + 0.55 * chunk, dp_deadline, false, LAMS[tid % 4], RUINS[tid % 3], true);
            lns(s, rng, ce, dp_deadline, true, LAMS[tid % 4], RUINS[tid % 3], false);
        } else lns(s, rng, ce, dp_deadline, fromBest, LAMS[tid % 4], RUINS[tid % 3]);
    }
}

int main(int argc, char** argv) {
    string inp = argc > 1 ? argv[1] : "instance.json";
    string outp = argc > 2 ? argv[2] : "solution.json";
    double limit = argc > 3 ? atof(argv[3]) : (getenv("TL") ? atof(getenv("TL")) : 280.0);

    DBG = getenv("DBG") != nullptr; DBG2 = getenv("DBG2") != nullptr;
    g_fd = open(outp.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0644);
    publish("[]\n");
    struct sigaction sa;
    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_signal;
    sigaction(SIGTERM, &sa, nullptr);
    sigaction(SIGINT, &sa, nullptr);
    sigaction(SIGALRM, &sa, nullptr);
    sigaction(SIGHUP, &sa, nullptr);
    sigaction(SIGUSR1, &sa, nullptr);
    alarm((unsigned)max(5.0, limit + 14));

    try {
        Inst I = load_instance(inp);
        if (I.ns == 0 || I.no == 0) return 0;
        Fast F(I);
        const uint64_t seed0 = getenv("SEED") ? strtoull(getenv("SEED"), nullptr, 10) * 0x9E3779B97F4A7C15ULL : 0;
        mt19937_64 rng(0x9E3779B97F4A7C15ULL ^ seed0);

        double t_outer = min(0.22 * limit, 60.0);
        map<vector<int>, Cand> cache;
        vector<Pt> G0(I.P.begin() + I.ns, I.P.end());
        auto ev = [&](vector<int> op) -> double {
            sort(op.begin(), op.end());
            if (op.empty()) return 0.0;
            auto it = cache.find(op);
            if (it != cache.end()) return it->second.f;
            Cand c;
            c.op = op;
            c.h.assign(I.no, 0.0);
            c.G = G0;
            c.f = F.search(op, c.h, c.G, 40, t_outer);
            cache.emplace(op, move(c));
            return cache[op].f;
        };
        // жадное добавление офисов
        vector<int> cur;
        double cur_f = 0;
        const bool lazy = !getenv("LAZY") || atoi(getenv("LAZY")) > 0;  // LAZY=0 — старый жадный
        if (lazy) {
            // ленивый жадный: приросты с прошлых шагов — оценки сверху, пересчитываем
            // только лидера; полный перебор на каждом шаге на 10⁴ сайтов не успевает
            vector<double> gain(I.no, 1e300);
            vector<char> in(I.no, 0);
            while (elapsed() < t_outer) {
                bool added = false;
                while (elapsed() < t_outer) {
                    int bo = -1;
                    for (int o = 0; o < I.no; o++)
                        if (!in[o] && (bo < 0 || gain[o] > gain[bo])) bo = o;
                    if (bo < 0 || gain[bo] <= 1e-9) break;
                    vector<int> v = cur; v.push_back(bo);
                    double g = ev(v) - cur_f;
                    gain[bo] = g;
                    double next = -1e300;
                    for (int o = 0; o < I.no; o++) if (!in[o] && o != bo) next = max(next, gain[o]);
                    if (g > 1e-9 && g >= next) {
                        cur.push_back(bo); in[bo] = 1; cur_f += g; added = true;
                        break;
                    }
                }
                if (!added) break;
            }
        }
        while (!lazy && elapsed() < t_outer) {
            double bf = NEG; int bo = -1;
            for (int o = 0; o < I.no && elapsed() < t_outer; o++) {
                if (find(cur.begin(), cur.end(), o) != cur.end()) continue;
                vector<int> v = cur; v.push_back(o);
                double f = ev(v);
                if (f > bf) { bf = f; bo = o; }
            }
            if (bo < 0 || bf <= cur_f + 1e-9) break;
            cur.push_back(bo); cur_f = bf;
        }
        // локальный поиск add / drop / swap
        bool improved = true;
        while (improved && elapsed() < t_outer) {
            improved = false;
            vector<vector<int>> moves;
            for (int o : cur) { vector<int> v; for (int x : cur) if (x != o) v.push_back(x); moves.push_back(v); }
            for (int n = 0; n < I.no; n++) if (find(cur.begin(), cur.end(), n) == cur.end()) {
                vector<int> v = cur; v.push_back(n); moves.push_back(v);
                for (int o : cur) { vector<int> w; for (int x : cur) if (x != o) w.push_back(x); w.push_back(n); moves.push_back(w); }
            }
            shuffle(moves.begin(), moves.end(), rng);
            for (auto& m : moves) {
                if (elapsed() > t_outer) break;
                double f = ev(m);
                if (f > cur_f + 1e-9) { cur = m; cur_f = f; improved = true; break; }
            }
        }
        // одиночные офисы как запасные варианты
        for (int o = 0; o < I.no && elapsed() < t_outer + 2; o++) { vector<int> v{o}; ev(v); }

        vector<Cand> cands;
        if (getenv("FORCE_OPS")) {               // отладка: задать набор офисов вручную
            Cand c;
            char* t = strdup(getenv("FORCE_OPS"));
            for (char* q = strtok(t, ","); q; q = strtok(nullptr, ",")) c.op.push_back(atoi(q));
            sort(c.op.begin(), c.op.end());
            c.h.assign(I.no, 0.0);
            c.G.assign(I.P.begin() + I.ns, I.P.end());
            c.f = F.search(c.op, c.h, c.G, 300, elapsed() + 5.0);
            cands.push_back(c);
        } else {
            vector<pair<double, const Cand*>> top;
            for (auto& kv : cache) if (kv.second.f > NEG / 2) top.push_back({kv.second.f, &kv.second});
            sort(top.rbegin(), top.rend());
            for (size_t i = 0; i < top.size() && i < 5; i++) cands.push_back(*top[i].second);
            // плюс лучший набор каждого размера: иначе варианты с другим числом
            // офисов (и другим делением навыков) просто не попадают в перебор
            map<size_t, const Cand*> bysize;
            for (auto& e : top) {
                size_t k = e.second->op.size();
                bool near = lazy && abs((int)k - (int)top[0].second->op.size()) <= 2;
                if ((k <= 8 || near) && !bysize.count(k)) bysize[k] = e.second;
            }
            for (auto& kv : bysize) {
                bool have = false;
                for (auto& c : cands) if (c.op == kv.second->op) { have = true; break; }
                if (!have) cands.push_back(*kv.second);
            }
        }
        if (cands.empty()) {
            Cand c;
            for (int o = 0; o < I.no; o++) c.op.push_back(o);
            c.f = 0;
            cands.push_back(c);
        }

        double dp_deadline = limit - max(1.0, 0.05 * limit);
        int nth = detect_cpus();
        if (I.ns > 20000) nth = min(nth, 6);
        vector<thread> th;
        // EXACT2=1: точный перебор 1–2 офисов отдельным потоком (сверх nth)
        if (getenv("EXACT2") && atoi(getenv("EXACT2")) > 0)
            th.emplace_back(exact2_thread, cref(I), limit, 0xE2ULL ^ seed0);
        for (int i = 1; i < nth; i++)
            th.emplace_back(worker, cref(I), cref(F), cref(cands),
                            (0xA5A5ULL * (i + 1) + 12345) ^ seed0, limit, dp_deadline, i);
        worker(I, F, cands, 777 ^ seed0, limit, dp_deadline, 0);
        for (auto& t : th) t.join();
        exact2_publish(I);

        fprintf(stderr, "objective=%.6f fast=%.3f sets=%zu threads=%d t=%.1f\n",
                g_best.load(), cur_f, cache.size(), nth, elapsed());
    } catch (const exception& ex) {
        fprintf(stderr, "error: %s\n", ex.what());
    }
    return 0;
}

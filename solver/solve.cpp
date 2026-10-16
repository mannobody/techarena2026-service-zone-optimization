// TechArena 2026, кейс 3 — решатель на C++ (один файл, только стандартная библиотека).
//
// Читает instance.json, пишет solution.json в текущем каталоге.
// Отладка: ./solve [instance.json] [solution.json] [секунды]; лимит также задаётся TL=...
//
// Схема (как в Python-версии solver/solve.py):
//   1) быстрая оценка множества офисов через power diagram (веса h и генераторы G):
//      ячейки выпуклы и не пересекаются, значит оболочки зон не делят точек;
//   2) выбор офисов: жадное добавление + локальный поиск add/drop/swap;
//   3) перенос лучших вариантов в точную модель (геометрия как у валидатора,
//      навыки с назначением рабочих, ёмкости, баланс числа сайтов),
//      имитация отжига по ходам «сайт -> офис / снять», затем спуск;
//   4) оставшееся время — повторные отжиги от лучшего решения.
// Ответ пишется при каждом улучшении, чтобы TLE не оставил пустой файл.

#include <algorithm>
#include <array>
#include <climits>
#include <memory>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using namespace std;
using Clock = chrono::steady_clock;
static const Clock::time_point T0 = Clock::now();
static double elapsed() { return chrono::duration<double>(Clock::now() - T0).count(); }

// ------------------------------------------------------------------ JSON
struct JVal {
    enum Kind { NUL, BOOL, NUM, STR, ARR, OBJ } kind = NUL;
    double num = 0;
    string str;
    vector<JVal> arr;
    vector<pair<string, JVal>> obj;
    const JVal& operator[](const string& k) const {
        for (auto& kv : obj)
            if (kv.first == k) return kv.second;
        throw runtime_error("missing key " + k);
    }
};

struct JParser {
    const string& s;
    size_t i = 0;
    explicit JParser(const string& src) : s(src) {
        if (s.size() >= 3 && (unsigned char)s[0] == 0xEF && (unsigned char)s[1] == 0xBB && (unsigned char)s[2] == 0xBF) i = 3;
    }
    void ws() { while (i < s.size() && isspace((unsigned char)s[i])) i++; }
    JVal parse() {
        ws();
        JVal v;
        char c = s.at(i);
        if (c == '{') {
            v.kind = JVal::OBJ; i++; ws();
            if (s[i] == '}') { i++; return v; }
            while (true) {
                ws(); string k = pstr(); ws(); i++;  // ':'
                v.obj.emplace_back(k, parse()); ws();
                if (s[i] == ',') { i++; continue; }
                i++; break;  // '}'
            }
        } else if (c == '[') {
            v.kind = JVal::ARR; i++; ws();
            if (s[i] == ']') { i++; return v; }
            while (true) {
                v.arr.push_back(parse()); ws();
                if (s[i] == ',') { i++; continue; }
                i++; break;  // ']'
            }
        } else if (c == '"') {
            v.kind = JVal::STR; v.str = pstr();
        } else if (c == 't') { v.kind = JVal::BOOL; v.num = 1; i += 4; }
        else if (c == 'f') { v.kind = JVal::BOOL; i += 5; }
        else if (c == 'n') { i += 4; }
        else {
            v.kind = JVal::NUM;
            const char* b = s.c_str() + i;
            char* e;
            v.num = strtod(b, &e);
            i += e - b;
        }
        return v;
    }
    string pstr() {
        string r; i++;  // '"'
        while (s[i] != '"') {
            if (s[i] == '\\') { i++; r += s[i] == 'n' ? '\n' : s[i]; if (s[i] == 'u') i += 4; }
            else r += s[i];
            i++;
        }
        i++;
        return r;
    }
};

// ---------------------------------------------------------------- геометрия
struct Pt { double x, y; };
static inline bool operator<(const Pt& a, const Pt& b) { return a.x < b.x || (a.x == b.x && a.y < b.y); }
static inline bool operator==(const Pt& a, const Pt& b) { return a.x == b.x && a.y == b.y; }
static inline double cr(const Pt& o, const Pt& a, const Pt& b) { return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x); }

// Монотонная цепь: вершины CCW без коллинеарных (1, 2 или >=3 точки).
static vector<Pt> hull_of(vector<Pt> p) {
    sort(p.begin(), p.end());
    p.erase(unique(p.begin(), p.end()), p.end());
    if (p.size() <= 2) return p;
    vector<Pt> h(2 * p.size());
    size_t k = 0;
    for (size_t i = 0; i < p.size(); i++) {
        while (k >= 2 && cr(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    for (size_t i = p.size() - 1, t = k + 1; i-- > 0;) {
        while (k >= t && cr(h[k - 2], h[k - 1], p[i]) <= 0) k--;
        h[k++] = p[i];
    }
    h.resize(k - 1);
    return h;
}

// ----------------------------------------------------------------- инстанс
struct Inst {
    int ns = 0, no = 0, nw = 0, nsk = 0, A = 0;
    double alpha = 0;
    vector<double> reward, ntask, cost;
    vector<int> maxsize;
    vector<vector<int>> skillset;     // уникальные навыки сайта
    vector<vector<char>> wskill;      // рабочий -> есть ли навык
    vector<int> wcount;               // число навыков у рабочего
    vector<vector<double>> D, profit; // [o][s]
    vector<char> servable;
    vector<Pt> P;                     // сайты, затем офисы
    double eps_len = 0, eps_cr = 0, ext = 1;
};

static Inst load(const string& path) {
    ifstream f(path, ios::binary);
    if (!f) throw runtime_error("no input");
    stringstream ss; ss << f.rdbuf();
    string src = ss.str();
    JParser jp(src);
    JVal J = jp.parse();
    Inst I;
    auto& S = J["sites"].arr;
    auto& O = J["offices"].arr;
    auto& W = J["workers"].arr;
    I.ns = S.size(); I.no = O.size(); I.nw = W.size();
    int maxsk = 0;
    for (auto& s : S) for (auto& t : s["tasks"].arr) maxsk = max(maxsk, (int)t.num + 1);
    for (auto& w : W) for (auto& t : w.arr) maxsk = max(maxsk, (int)t.num + 1);
    I.nsk = maxsk;
    for (auto& s : S) {
        I.P.push_back({s["x"].num, s["y"].num});
        I.reward.push_back(s["reward"].num);
        I.ntask.push_back((double)s["tasks"].arr.size());
        set<int> u;
        for (auto& t : s["tasks"].arr) u.insert((int)t.num);
        I.skillset.emplace_back(u.begin(), u.end());
    }
    for (auto& o : O) {
        I.P.push_back({o["x"].num, o["y"].num});
        I.cost.push_back(o["cost"].num);
        I.maxsize.push_back((int)o["maxSize"].num);
    }
    vector<char> any(I.nsk, 0);
    for (auto& w : W) {
        vector<char> m(I.nsk, 0);
        int c = 0;
        for (auto& t : w.arr) { if (!m[(int)t.num]) c++; m[(int)t.num] = 1; any[(int)t.num] = 1; }
        I.wskill.push_back(m);
        I.wcount.push_back(c);
    }
    auto& Dm = J["distances"].arr;
    I.D.assign(I.no, vector<double>(I.ns));
    I.profit.assign(I.no, vector<double>(I.ns));
    for (int o = 0; o < I.no; o++)
        for (int s = 0; s < I.ns; s++) {
            I.D[o][s] = Dm[o].arr[s].num;
            I.profit[o][s] = I.reward[s] - I.D[o][s];
        }
    I.A = (int)J["maxDifference"].num;
    I.alpha = J["balanceCoefficient"].num;
    I.servable.assign(I.ns, 1);
    for (int s = 0; s < I.ns; s++)
        for (int k : I.skillset[s]) if (!any[k]) I.servable[s] = 0;
    double mnx = 1e300, mxx = -1e300, mny = 1e300, mxy = -1e300;
    for (auto& p : I.P) { mnx = min(mnx, p.x); mxx = max(mxx, p.x); mny = min(mny, p.y); mxy = max(mxy, p.y); }
    I.ext = I.P.empty() ? 1.0 : max(mxx - mnx, mxy - mny);
    if (I.ext <= 0) I.ext = 1.0;
    I.eps_len = 1e-9 * I.ext;
    I.eps_cr = 1e-9 * I.ext * I.ext;
    return I;
}

// Маска точек, покрытых оболочкой (с допуском в сторону «покрыто»).
static void covers(const Inst& I, const vector<Pt>& h, vector<char>& out) {
    size_t n = I.P.size();
    out.assign(n, 0);
    if (h.size() == 1) {
        for (size_t i = 0; i < n; i++) out[i] = hypot(I.P[i].x - h[0].x, I.P[i].y - h[0].y) <= I.eps_len;
        return;
    }
    if (h.size() == 2) {
        double ax = h[0].x, ay = h[0].y, dx = h[1].x - ax, dy = h[1].y - ay;
        double L2 = dx * dx + dy * dy, L = sqrt(L2);
        for (size_t i = 0; i < n; i++) {
            double X = I.P[i].x, Y = I.P[i].y;
            double c = dx * (Y - ay) - dy * (X - ax), d = dx * (X - ax) + dy * (Y - ay);
            out[i] = fabs(c) <= I.eps_cr + I.eps_len * L && d >= -I.eps_len * L && d <= L2 + I.eps_len * L;
        }
        return;
    }
    size_t m = h.size();
    vector<double> tol(m);
    for (size_t e = 0; e < m; e++) {
        const Pt &a = h[e], &b = h[(e + 1) % m];
        tol[e] = -I.eps_cr - I.eps_len * hypot(b.x - a.x, b.y - a.y);
    }
    for (size_t i = 0; i < n; i++) {
        bool in = true;
        for (size_t e = 0; e < m && in; e++) {
            const Pt &a = h[e], &b = h[(e + 1) % m];
            in = (b.x - a.x) * (I.P[i].y - a.y) - (b.y - a.y) * (I.P[i].x - a.x) >= tol[e];
        }
        out[i] = in;
    }
}

// ---------------------------------------------------------------- решение
struct Sol {
    const Inst* I;
    vector<int> opened;
    vector<char> isopen;
    vector<int> asg, size, wof;
    vector<double> load;
    vector<vector<int>> members;     // по офисам
    vector<int> pos;                 // позиция сайта в members[asg]
    vector<vector<int>> need;        // [o][skill]
    vector<vector<Pt>> hull;
    vector<vector<char>> inhull;
    vector<int> cov;
    double prof_sum = 0;

    Sol(const Inst& In, const vector<int>& op) : I(&In), opened(op) {
        isopen.assign(I->no, 0);
        for (int o : op) isopen[o] = 1;
        asg.assign(I->ns, -1);
        pos.assign(I->ns, -1);
        size.assign(I->no, 0);
        load.assign(I->no, 0);
        wof.assign(I->nw, -1);
        members.assign(I->no, {});
        need.assign(I->no, vector<int>(I->nsk, 0));
        hull.assign(I->no, {});
        inhull.assign(I->no, {});
        cov.assign(I->P.size(), 0);
        for (int o : op) set_hull(o, {I->P[I->ns + o]});
    }

    void set_hull(int o, vector<Pt> h) {
        auto& m = inhull[o];
        if (!m.empty())
            for (size_t i = 0; i < m.size(); i++) cov[i] -= m[i];
        covers(*I, h, m);
        for (size_t i = 0; i < m.size(); i++) cov[i] += m[i];
        hull[o] = move(h);
    }
    void rebuild_hull(int o) {
        vector<Pt> pts;
        pts.reserve(members[o].size() + 1);
        for (int s : members[o]) pts.push_back(I->P[s]);
        pts.push_back(I->P[I->ns + o]);
        set_hull(o, hull_of(pts));
    }
    // ok и новая оболочка (пустая, если не меняется)
    bool can_add_geo(int s, int o, vector<Pt>& h) {
        h.clear();
        if (inhull[o][s]) return true;
        vector<Pt> pts = hull[o];
        pts.push_back(I->P[s]);
        h = hull_of(pts);
        static vector<char> m;
        covers(*I, h, m);
        const auto& old = inhull[o];
        for (size_t i = 0; i < m.size(); i++)
            if (m[i] && !old[i] && cov[i] > 0) return false;
        return true;
    }

    // --- навыки
    vector<char> office_skills(int o) const {
        vector<char> sk(I->nsk, 0);
        for (int w = 0; w < I->nw; w++)
            if (wof[w] == o)
                for (int k = 0; k < I->nsk; k++) sk[k] |= I->wskill[w][k];
        return sk;
    }
    bool plan_skills(int s, int o, vector<int>& add) const {
        add.clear();
        vector<char> have = office_skills(o);
        for (int k : I->skillset[s]) {
            if (have[k]) continue;
            int best = -1;
            for (int w = 0; w < I->nw; w++)
                if (wof[w] == -1 && I->wskill[w][k] && find(add.begin(), add.end(), w) == add.end())
                    if (best < 0 || I->wcount[w] < I->wcount[best]) best = w;
            if (best < 0) return false;
            add.push_back(best);
            for (int kk = 0; kk < I->nsk; kk++) have[kk] |= I->wskill[best][kk];
        }
        return true;
    }
    void release_workers(int o) {
        vector<int> ws;
        for (int w = 0; w < I->nw; w++) if (wof[w] == o) ws.push_back(w);
        sort(ws.begin(), ws.end(), [&](int a, int b) { return I->wcount[a] < I->wcount[b]; });
        for (int w : ws) {
            vector<char> rest(I->nsk, 0);
            for (int w2 : ws) if (w2 != w && wof[w2] == o) for (int k = 0; k < I->nsk; k++) rest[k] |= I->wskill[w2][k];
            bool ok = true;
            for (int k = 0; k < I->nsk && ok; k++) if (need[o][k] > 0 && !rest[k]) ok = false;
            if (ok) wof[w] = -1;
        }
    }

    // --- целевая: считаются только непустые офисы (как в ответе)
    double eval_tail(const vector<int>& sz, const vector<double>& ld) const {
        double c = 0, mx = -1e300, mn = 1e300;
        for (int o : opened) if (sz[o] > 0) { c += I->cost[o]; mx = max(mx, ld[o]); mn = min(mn, ld[o]); }
        if (mx < mn) return 0;
        return -c - I->alpha * (mx - mn);
    }
    double objective() const { return prof_sum + eval_tail(size, load); }
    bool sizes_ok(const vector<int>& sz) const {
        int mx = INT32_MIN, mn = INT32_MAX;
        for (int o : opened) if (sz[o] > 0) {
            if (sz[o] > I->maxsize[o]) return false;
            mx = max(mx, sz[o]); mn = min(mn, sz[o]);
        }
        return mx < mn || mx - mn <= I->A;
    }

    // --- ходы
    void remove(int s) {
        int o = asg[s];
        asg[s] = -1;
        int p = pos[s], last = members[o].back();
        members[o][p] = last; pos[last] = p; members[o].pop_back(); pos[s] = -1;
        size[o]--; load[o] -= I->ntask[s]; prof_sum -= I->profit[o][s];
        for (int k : I->skillset[s]) need[o][k]--;
        const Pt& q = I->P[s];
        if (find(hull[o].begin(), hull[o].end(), q) != hull[o].end()) rebuild_hull(o);
        release_workers(o);
    }
    void add(int s, int o, vector<Pt>& h, const vector<int>& wk) {
        asg[s] = o;
        pos[s] = members[o].size(); members[o].push_back(s);
        size[o]++; load[o] += I->ntask[s]; prof_sum += I->profit[o][s];
        for (int k : I->skillset[s]) need[o][k]++;
        for (int w : wk) wof[w] = o;
        if (!h.empty()) set_hull(o, move(h));
    }
    bool force_move(int s, int onew) {
        int oold = asg[s];
        if (onew == oold) return false;
        vector<int> sz = size;
        if (oold >= 0) sz[oold]--;
        if (onew >= 0) sz[onew]++;
        if (!sizes_ok(sz)) return false;
        if (oold >= 0) remove(s);
        if (onew < 0) return true;
        vector<Pt> h; vector<int> wk;
        bool ok = can_add_geo(s, onew, h) && plan_skills(s, onew, wk);
        if (!ok) {
            if (oold >= 0) {
                vector<Pt> h2; vector<int> wk2;
                can_add_geo(s, oold, h2);
                plan_skills(s, oold, wk2);
                add(s, oold, h2, wk2);
            }
            return false;
        }
        add(s, onew, h, wk);
        return true;
    }
    // изменение точной цели при переводе s в onew (без проверки допустимости)
    double delta(int s, int onew) const {
        int oold = asg[s];
        vector<int> sz = size; vector<double> ld = load;
        double d = 0;
        if (oold >= 0) { d -= I->profit[oold][s]; sz[oold]--; ld[oold] -= I->ntask[s]; }
        if (onew >= 0) { d += I->profit[onew][s]; sz[onew]++; ld[onew] += I->ntask[s]; }
        return d + eval_tail(sz, ld) - eval_tail(size, load);
    }

    struct State { vector<int> asg, wof; };
    State snapshot() const { return {asg, wof}; }
    static Sol from_state(const Inst& I, const vector<int>& op, const State& st) {
        Sol sol(I, op);
        sol.wof = st.wof;
        for (int s = 0; s < I.ns; s++) {
            int o = st.asg[s];
            if (o < 0) continue;
            sol.asg[s] = o; sol.pos[s] = sol.members[o].size(); sol.members[o].push_back(s);
            sol.size[o]++; sol.load[o] += I.ntask[s]; sol.prof_sum += I.profit[o][s];
            for (int k : I.skillset[s]) sol.need[o][k]++;
        }
        for (int o : op) sol.rebuild_hull(o);
        return sol;
    }
};

// Снимаем наименее выгодные сайты, пока не выполнены maxSize и баланс A.
static void repair_sizes(Sol& sol) {
    const Inst& I = *sol.I;
    while (!sol.sizes_ok(sol.size)) {
        int pick = -1;
        for (int o : sol.opened) if (sol.size[o] > I.maxsize[o]) { pick = o; break; }
        if (pick < 0) {
            int mx = -1;
            for (int o : sol.opened) if (sol.size[o] > mx) { mx = sol.size[o]; pick = o; }
        }
        int best = -1;
        for (int s : sol.members[pick]) if (best < 0 || I.profit[pick][s] < I.profit[pick][best]) best = s;
        sol.remove(best);
    }
}

// ------------------------------------------------ быстрая оценка (power diagram)
struct Fast {
    const Inst& I;
    vector<int> skills, wcnt;
    vector<vector<char>> req;  // [s][j]
    double scale2 = 1;

    explicit Fast(const Inst& In) : I(In) {
        set<int> u;
        for (auto& ss : I.skillset) for (int k : ss) u.insert(k);
        skills.assign(u.begin(), u.end());
        for (int k : skills) {
            int c = 0;
            for (int w = 0; w < I.nw; w++) c += I.wskill[w][k];
            wcnt.push_back(c);
        }
        req.assign(I.ns, vector<char>(skills.size(), 0));
        for (int s = 0; s < I.ns; s++)
            for (int k : I.skillset[s]) req[s][lower_bound(skills.begin(), skills.end(), k) - skills.begin()] = 1;
        vector<double> mins;
        for (int s = 0; s < I.ns; s++) {
            double m = 1e300;
            for (int o = 0; o < I.no; o++) {
                const Pt &a = I.P[s], &b = I.P[I.ns + o];
                m = min(m, (a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y));
            }
            mins.push_back(m);
        }
        if (!mins.empty()) {
            nth_element(mins.begin(), mins.begin() + mins.size() / 2, mins.end());
            scale2 = mins[mins.size() / 2] + 1e-12;
        }
    }

    // h: веса, G: генераторы (по индексам офисов); members — выход
    double evaluate(const vector<int>& op, const vector<double>& h, const vector<Pt>& G,
                    vector<vector<int>>* out = nullptr) const {
        int K = op.size();
        // офис обязан лежать в своей ячейке
        for (int a = 0; a < K; a++) {
            const Pt& p = I.P[I.ns + op[a]];
            int arg = 0; double best = 1e300;
            for (int b = 0; b < K; b++) {
                const Pt& g = G[op[b]];
                double v = (p.x - g.x) * (p.x - g.x) + (p.y - g.y) * (p.y - g.y) - h[op[b]];
                if (v < best) { best = v; arg = b; }
            }
            if (arg != a) return -1e300;
        }
        vector<int> c(I.ns);
        vector<double> prof(I.ns);
        vector<char> ok(I.ns);
        for (int s = 0; s < I.ns; s++) {
            const Pt& p = I.P[s];
            int arg = 0; double best = 1e300;
            for (int b = 0; b < K; b++) {
                const Pt& g = G[op[b]];
                double v = (p.x - g.x) * (p.x - g.x) + (p.y - g.y) * (p.y - g.y) - h[op[b]];
                if (v < best) { best = v; arg = b; }
            }
            c[s] = arg;
            prof[s] = I.profit[op[arg]][s];
            ok[s] = prof[s] > 0 && I.servable[s];
        }
        // дефицитные навыки отдаём офисам, где они приносят больше выгоды
        int J = skills.size();
        vector<vector<char>> allow(K, vector<char>(J, 1));
        for (int j = 0; j < J; j++) {
            if (wcnt[j] >= K) continue;
            vector<double> val(K, 0);
            for (int s = 0; s < I.ns; s++) if (ok[s] && req[s][j]) val[c[s]] += prof[s];
            vector<int> idx(K);
            iota(idx.begin(), idx.end(), 0);
            stable_sort(idx.begin(), idx.end(), [&](int a, int b) { return val[a] > val[b]; });
            for (int r = wcnt[j]; r < K; r++) allow[idx[r]][j] = 0;
        }
        for (int s = 0; s < I.ns; s++) if (ok[s])
            for (int j = 0; j < J; j++) if (req[s][j] && !allow[c[s]][j]) { ok[s] = 0; break; }
        vector<vector<int>> mem(K);
        for (int s = 0; s < I.ns; s++) if (ok[s]) mem[c[s]].push_back(s);
        int smin = INT32_MAX;
        for (int b = 0; b < K; b++) {
            auto& m = mem[b];
            sort(m.begin(), m.end(), [&](int x, int y) { return prof[x] > prof[y]; });
            if ((int)m.size() > I.maxsize[op[b]]) m.resize(I.maxsize[op[b]]);
            smin = min(smin, (int)m.size());
        }
        for (int b = 0; b < K; b++) if ((int)mem[b].size() > smin + I.A) mem[b].resize(smin + I.A);
        double base_cost = 0;
        for (int o : op) base_cost += I.cost[o];
        double P0 = 0;
        for (int b = 0; b < K; b++) for (int s : mem[b]) P0 += prof[s];
        if (I.alpha <= 0) {
            if (out) { out->assign(I.no, {}); for (int b = 0; b < K; b++) (*out)[op[b]] = mem[b]; }
            return P0 - base_cost;
        }
        // уровень нагрузки t: в перегруженных офисах снимаем сайты, дешёвые за задачу
        vector<vector<int>> rm(K);
        vector<vector<double>> ct(K), cp(K);
        vector<double> L(K, 0);
        for (int b = 0; b < K; b++) {
            for (int s : mem[b]) { L[b] += I.ntask[s]; if (I.ntask[s] > 0) rm[b].push_back(s); }
            sort(rm[b].begin(), rm[b].end(), [&](int x, int y) { return prof[x] / I.ntask[x] < prof[y] / I.ntask[y]; });
            double a = 0, q = 0;
            for (int s : rm[b]) { a += I.ntask[s]; q += prof[s]; ct[b].push_back(a); cp[b].push_back(q); }
        }
        double lo = *min_element(L.begin(), L.end()), hi = *max_element(L.begin(), L.end());
        vector<double> levels(L.begin(), L.end());
        levels.push_back(hi);
        for (int i = 0; i < 40; i++) levels.push_back(lo + (hi - lo) * i / 39.0);
        sort(levels.begin(), levels.end());
        levels.erase(unique(levels.begin(), levels.end()), levels.end());
        double bestf = -1e300;
        vector<int> bestcut;
        vector<int> cut(K);
        for (double t : levels) {
            double cost = 0, mx = -1e300, mn = 1e300;
            int smx = INT32_MIN, smn = INT32_MAX;
            for (int b = 0; b < K; b++) {
                double ex = L[b] - t, nl = L[b];
                int k = 0;
                if (ex > 0 && !rm[b].empty()) {
                    k = lower_bound(ct[b].begin(), ct[b].end(), ex - 1e-9) - ct[b].begin() + 1;
                    k = min(k, (int)rm[b].size());
                    cost += cp[b][k - 1];
                    nl -= ct[b][k - 1];
                }
                cut[b] = k;
                int sz = mem[b].size() - k;
                smx = max(smx, sz); smn = min(smn, sz);
                mx = max(mx, nl); mn = min(mn, nl);
            }
            if (smx - smn > I.A) continue;
            double f = P0 - cost - base_cost - I.alpha * (mx - mn);
            if (f > bestf) { bestf = f; bestcut = cut; }
        }
        if (out && !bestcut.empty()) {
            out->assign(I.no, {});
            for (int b = 0; b < K; b++) {
                set<int> drop(rm[b].begin(), rm[b].begin() + bestcut[b]);
                for (int s : mem[b]) if (!drop.count(s)) (*out)[op[b]].push_back(s);
            }
        }
        return bestf;
    }

    // координатный поиск по весам h и положениям генераторов G
    double search(const vector<int>& op, vector<double>& h, vector<Pt>& G, int iters, double deadline) const {
        double best = evaluate(op, h, G);
        vector<array<double, 3>> step(I.no);
        for (int o : op) step[o] = {0.5 * scale2, 0.05 * I.ext, 0.05 * I.ext};
        for (int it = 0; it < iters; it++) {
            if (elapsed() > deadline) break;
            bool improved = false, alive = false;
            for (int o : op)
                for (int p = 0; p < 3; p++) {
                    bool moved = false;
                    for (double sg : {1.0, -1.0}) {
                        double d = sg * step[o][p];
                        double& v = p == 0 ? h[o] : (p == 1 ? G[o].x : G[o].y);
                        v += d;
                        double f = evaluate(op, h, G);
                        if (f > best + 1e-9) { best = f; improved = moved = true; step[o][p] *= 1.6; break; }
                        v -= d;
                    }
                    if (!moved) step[o][p] *= 0.5;
                    if (step[o][p] > 1e-6 * (p == 0 ? scale2 : I.ext)) alive = true;
                }
            if (!improved && !alive) break;
        }
        return best;
    }
};

// Переносит назначение в точную модель (недопустимые сайты пропускаются).
static Sol build_sol(const Inst& I, const vector<int>& op, const vector<vector<int>>& mem) {
    Sol sol(I, op);
    vector<pair<int, int>> order;
    for (int o : op) for (int s : mem[o]) order.push_back({s, o});
    sort(order.begin(), order.end(), [&](auto& a, auto& b) { return I.profit[a.second][a.first] > I.profit[b.second][b.first]; });
    for (auto [s, o] : order) {
        if (sol.size[o] + 1 > I.maxsize[o]) continue;
        vector<Pt> h; vector<int> wk;
        if (sol.can_add_geo(s, o, h) && sol.plan_skills(s, o, wk)) sol.add(s, o, h, wk);
    }
    repair_sizes(sol);
    return sol;
}

// ---------------------------------------------------------- отжиг и спуск
static Sol anneal(Sol sol, mt19937_64& rng, double t_end, double lam_frac = 0.2) {
    const Inst& I = *sol.I;
    vector<int> cand;
    for (int s = 0; s < I.ns; s++) if (I.servable[s]) cand.push_back(s);
    if (cand.empty() || sol.opened.empty()) return sol;
    double lam = I.alpha * lam_frac;
    vector<vector<int>> nearest(I.ns);
    for (int s : cand) {
        vector<int> v = sol.opened;
        sort(v.begin(), v.end(), [&](int a, int b) { return I.D[a][s] < I.D[b][s]; });
        if (v.size() > 5) v.resize(5);
        nearest[s] = v;
    }
    double ps = 0; long cnt = 0;
    for (int o : sol.opened) for (int s : cand) { ps += fabs(I.profit[o][s]); cnt++; }
    ps = ps / max(1L, cnt) + 1e-9;
    double T_hi = 0.3 * ps, T_lo = 1e-4 * ps, T = T_hi;
    auto spread = [&](const vector<int>& sz, const vector<double>& ld) {
        double m = 0; int n = 0;
        for (int o : sol.opened) if (sz[o] > 0) { m += ld[o]; n++; }
        if (!n) return 0.0;
        m /= n;
        double r = 0;
        for (int o : sol.opened) if (sz[o] > 0) r += fabs(ld[o] - m);
        return r;
    };
    double best_f = sol.objective();
    auto best = sol.snapshot();
    double t_start = elapsed(), dur = max(1e-3, t_end - t_start);
    uniform_real_distribution<double> U(0, 1);
    for (long it = 1;; it++) {
        if ((it & 63) == 0) {
            double now = elapsed();
            if (now >= t_end) break;
            T = T_hi * pow(T_lo / T_hi, (now - t_start) / dur);
        }
        int s = cand[rng() % cand.size()];
        int oold = sol.asg[s];
        auto& nr = nearest[s];
        int onew = (oold >= 0 && U(rng) < 0.25) ? -1 : nr[rng() % nr.size()];
        if (onew == oold) continue;
        vector<int> sz = sol.size; vector<double> ld = sol.load;
        double d = 0;
        if (oold >= 0) { d -= I.profit[oold][s]; sz[oold]--; ld[oold] -= I.ntask[s]; }
        if (onew >= 0) { d += I.profit[onew][s]; sz[onew]++; ld[onew] += I.ntask[s]; }
        d += sol.eval_tail(sz, ld) - sol.eval_tail(sol.size, sol.load);
        d -= lam * (spread(sz, ld) - spread(sol.size, sol.load));
        if (d < 0 && U(rng) >= exp(d / T)) continue;
        if (sol.force_move(s, onew)) {
            double f = sol.objective();
            if (f > best_f + 1e-9) { best_f = f; best = sol.snapshot(); }
        }
    }
    return Sol::from_state(I, sol.opened, best);
}

static void local_search(Sol& sol, mt19937_64& rng, double t_end) {
    const Inst& I = *sol.I;
    vector<vector<int>> nearest(I.ns);
    for (int s = 0; s < I.ns; s++) {
        vector<int> v = sol.opened;
        sort(v.begin(), v.end(), [&](int a, int b) { return I.D[a][s] < I.D[b][s]; });
        if (v.size() > 4) v.resize(4);
        v.push_back(-1);
        nearest[s] = v;
    }
    vector<int> order(I.ns);
    iota(order.begin(), order.end(), 0);
    bool improved = true;
    while (improved && elapsed() < t_end) {
        improved = false;
        shuffle(order.begin(), order.end(), rng);
        for (int s : order) {
            if (elapsed() > t_end) break;
            if (!I.servable[s]) continue;
            vector<pair<double, int>> g;
            for (int o : nearest[s]) if (o != sol.asg[s]) { double d = sol.delta(s, o); if (d > 1e-9) g.push_back({d, o}); }
            sort(g.rbegin(), g.rend());
            for (auto& [d, o] : g) if (sol.force_move(s, o)) { improved = true; break; }
        }
    }
}

// ------------------------------------------------------------------ вывод
static void write_solution(const string& path, const Sol* sol) {
    FILE* f = fopen(path.c_str(), "w");  // пишем прямо в файл, без rename
    if (!f) return;
    fputc('[', f);
    bool first = true;
    if (sol) {
        for (int o : sol->opened) {
            if (sol->size[o] == 0) continue;
            vector<int> ss = sol->members[o];
            sort(ss.begin(), ss.end());
            fprintf(f, "%s{\"officeId\":%d,\"sites\":[", first ? "" : ",", o);
            for (size_t i = 0; i < ss.size(); i++) fprintf(f, "%s%d", i ? "," : "", ss[i]);
            fprintf(f, "],\"workers\":[");
            bool fw = true;
            for (int w = 0; w < sol->I->nw; w++) if (sol->wof[w] == o) { fprintf(f, "%s%d", fw ? "" : ",", w); fw = false; }
            fprintf(f, "]}");
            first = false;
        }
    }
    fputs("]\n", f);
    fclose(f);
}

int main(int argc, char** argv) {
    string inp = argc > 1 ? argv[1] : "instance.json";
    string outp = argc > 2 ? argv[2] : "solution.json";
    double limit = argc > 3 ? atof(argv[3]) : (getenv("TL") ? atof(getenv("TL")) : 270.0);
    write_solution(outp, nullptr);  // пустое решение валидно и даёт 0
    try {
        Inst I = load(inp);
        if (I.ns == 0 || I.no == 0) return 0;
        mt19937_64 rng(12345);
        double best_f = 0;
        unique_ptr<Sol> best;
        auto offer = [&](Sol& s) {
            double f = s.objective();
            if (f > best_f + 1e-9) {
                best_f = f;
                best = make_unique<Sol>(s);
                write_solution(outp, best.get());
            }
        };
        Fast F(I);
        double t_outer = 0.40 * limit;
        struct Ent { double f; vector<double> h; vector<Pt> G; };
        map<vector<int>, Ent> cache;
        vector<Pt> G0(I.P.begin() + I.ns, I.P.end());
        auto ev = [&](vector<int> op) -> double {
            sort(op.begin(), op.end());
            if (op.empty()) return 0.0;
            auto it = cache.find(op);
            if (it != cache.end()) return it->second.f;
            vector<double> h(I.no, 0.0);
            vector<Pt> G = G0;
            double f = F.search(op, h, G, 60, t_outer);
            cache[op] = {f, h, G};
            return f;
        };
        // 1) жадное добавление офисов
        vector<int> cur; double cur_f = 0;
        while (elapsed() < t_outer) {
            double bf = -1e300; int bo = -1;
            for (int o = 0; o < I.no && elapsed() < t_outer; o++) {
                if (find(cur.begin(), cur.end(), o) != cur.end()) continue;
                vector<int> v = cur; v.push_back(o);
                double f = ev(v);
                if (f > bf) { bf = f; bo = o; }
            }
            if (bo < 0 || bf <= cur_f + 1e-9) break;
            cur.push_back(bo); cur_f = bf;
        }
        // 2) локальный поиск add / drop / swap
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
        sort(cur.begin(), cur.end());
        // 3) лучшие множества: точная модель + отжиг
        vector<pair<double, vector<int>>> top;
        for (auto& [k, e] : cache) top.push_back({e.f, k});
        sort(top.rbegin(), top.rend());
        vector<vector<int>> cands;
        if (!cur.empty()) cands.push_back(cur);
        for (auto& [f, k] : top) {
            if ((int)cands.size() >= 3) break;
            if (k != cur && f > -1e299) cands.push_back(k);
        }
        for (size_t idx = 0; idx < cands.size(); idx++) {
            double left = limit - elapsed();
            if (left <= 0.5) break;
            double share = left * (idx == 0 ? 0.45 : 0.4);
            auto& op = cands[idx];
            Ent& e = cache[op];
            F.search(op, e.h, e.G, 300, elapsed() + 0.25 * share);
            vector<vector<int>> mem;
            if (F.evaluate(op, e.h, e.G, &mem) <= -1e299 || mem.empty()) continue;
            Sol sol = build_sol(I, op, mem);
            offer(sol);
            sol = anneal(sol, rng, elapsed() + 0.6 * share);
            local_search(sol, rng, elapsed() + 0.15 * share);
            offer(sol);
        }
        // 4) оставшееся время: повторные отжиги от лучшего решения
        while (best && elapsed() < limit - 1.0) {
            double left = limit - elapsed();
            double chunk = min(left - 0.5, max(2.0, left / 3));
            if (chunk <= 0.2) break;
            Sol sol = Sol::from_state(I, best->opened, best->snapshot());
            sol = anneal(sol, rng, elapsed() + 0.85 * chunk, 0.2);
            local_search(sol, rng, elapsed() + 0.15 * chunk);
            offer(sol);
        }
        fprintf(stderr, "objective=%.3f fast_best=%.3f evals=%zu t=%.1fs\n", best_f, cur_f, cache.size(), elapsed());
    } catch (const exception& ex) {
        fprintf(stderr, "error: %s\n", ex.what());  // лучшее решение уже записано
    }
    return 0;
}

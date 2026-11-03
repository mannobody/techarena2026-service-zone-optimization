// Regression: incremental coverage, deferred removals and undo must match a full rebuild.
// g++ -O3 -std=c++17 tools/test_geometry_state.cpp -o /tmp/test_geometry_state
// /tmp/test_geometry_state [GEO_EXACT=0/1] [GEO_INDEX=0/1]
#define main service_zone_main
#include "hybrid_v2.cpp"
#undef main
#include <cassert>

static bool reference_covers(const Inst& I, const vector<Pt>& h, Pt p) {
    if (g_geo_exact) return geo_exact_covers(h, p);
    if (h.size() == 1)
        return fabs(p.x - h[0].x) <= I.eps_len && fabs(p.y - h[0].y) <= I.eps_len;
    if (h.size() == 2) {
        double dx = h[1].x - h[0].x, dy = h[1].y - h[0].y;
        double x = p.x - h[0].x, y = p.y - h[0].y;
        double l2 = dx * dx + dy * dy, l = sqrt(l2);
        return fabs(dx * y - dy * x) <= I.eps_cr + I.eps_len * l &&
               dx * x + dy * y >= -I.eps_len * l && dx * x + dy * y <= l2 + I.eps_len * l;
    }
    if (h.empty()) return false;
    double x0 = 1e300, x1 = -1e300, y0 = 1e300, y1 = -1e300;
    for (Pt q : h) { x0 = min(x0, q.x); x1 = max(x1, q.x); y0 = min(y0, q.y); y1 = max(y1, q.y); }
    if (p.x < x0 - I.eps_len || p.x > x1 + I.eps_len ||
        p.y < y0 - I.eps_len || p.y > y1 + I.eps_len) return false;
    for (size_t j = 0; j < h.size(); ++j) {
        Pt a = h[j], b = h[(j + 1) % h.size()];
        double dx = b.x - a.x, dy = b.y - a.y;
        if (dx * (p.y - a.y) - dy * (p.x - a.x) < -I.eps_cr - I.eps_len * hypot(dx, dy)) return false;
    }
    return true;
}

static void check_state(const Sol& s) {
    const Inst& I = *s.I;
    assert(!s.defer);
    uint64_t expected_sig = 0;
    for (int o = 0; o < I.no; ++o) {
        if (s.isopen[o]) expected_sig ^= s.sigkey[(size_t)I.no * I.nsk + o];
        for (int k = 0; k < I.nsk; ++k)
            if (s.need[o][k] > 0) expected_sig ^= s.sigkey[(size_t)o * I.nsk + k];
    }
    assert(s.sig == expected_sig);
    vector<int> counts(s.np, 0);
    for (int o = 0; o < I.no; ++o) {
        assert(!s.dirty[o]);
        vector<Pt> h;
        for (int x = 0; x < I.ns; ++x) if (s.asg[x] == o) h.push_back(I.P[x]);
        assert(h.size() == s.members[o].size());
        if (s.isopen[o]) h.push_back(I.P[I.ns + o]);
        hull_of(h);
        vector<int> listed(s.np, 0);
        for (int x : s.covlist[o]) ++listed[x];
        for (int x = 0; x < s.np; ++x) {
            bool expected = reference_covers(I, h, I.P[x]);
            assert(s.incov[(size_t)o * s.np + x] == expected);
            assert(listed[x] == (int)expected);
            counts[x] += expected;
        }
    }
    for (int x = 0; x < s.np; ++x) {
        assert(s.cov[x] == counts[x]);
        assert(counts[x] <= 1);
    }
}

int main(int argc, char** argv) {
    g_geo_exact = argc < 2 || atoi(argv[1]);
    setenv("GEO_INDEX", argc < 3 ? "1" : argv[2], 1);
    long additions = 0, checks = 0;
    for (int seed = 1; seed <= 16; ++seed) {
        mt19937_64 rng(seed);
        Inst I;
        I.ns = 96; I.no = 4; I.nw = 4; I.nsk = 1; I.A = I.ns;
        I.ext = 40; I.eps_len = 1e-10; I.eps_cr = 1e-10;
        I.reward.assign(I.ns, 100); I.cost.assign(I.no, 0);
        I.D.assign(I.ns * I.no, 0); I.prof.assign(I.ns * I.no, 100);
        I.ntask.assign(I.ns, 1); I.maxsize.assign(I.no, I.ns);
        I.servable.assign(I.ns, 1); I.Nk.assign(1, I.nw);
        I.skillset.assign(I.ns, vector<int>{0});
        I.wskills.assign(I.nw, vector<int>{0}); I.wmask.assign(I.nw, vector<char>{1});
        I.P.resize(I.ns);
        for (Pt& p : I.P) p = {(double)(int(rng() % 33) - 16), (double)(int(rng() % 33) - 16)};
        for (Pt p : vector<Pt>{{-20,-20}, {20,-20}, {20,20}, {-20,20}}) I.P.push_back(p);
        g_geo_grid.init(I);
        Sol s; s.init(I); Engine E(s);
        for (int o = 0; o < I.no; ++o) E.doOpen(o);
        for (int it = 0; it < 400; ++it) {
            int x = rng() % I.ns, o = rng() % I.no;
            switch (rng() % 11) {
            case 0: case 1: case 2: additions += E.doAdd(x, o); break;
            case 3: E.doRemove(x); break;
            case 4: E.doClose(o); break;
            case 5: E.doOpen(o); break;
            case 6: {
                auto old = s.asg; auto opened = s.isopen;
                E.rec = true; size_t mark = E.jr.size();
                for (int j = 0; j < 4; ++j) E.doRemove(rng() % I.ns);
                for (int j = 0; j < 4; ++j) additions += E.doAdd(rng() % I.ns, rng() % I.no);
                E.undo(mark); E.rec = false;
                assert(s.asg == old && s.isopen == opened);
                break;
            }
            case 7:
                s.begin_defer();
                for (int j = 0; j < 4; ++j) E.doRemove(rng() % I.ns);
                s.end_defer(); break;
            case 8: {
                auto old = s.asg; auto opened = s.isopen;
                vector<Pt> h; s.geo_ok(x, o, h);
                s.load_state(old, opened);
                // Frozen v4 has no speculative gs/go coverage cache.
                break;
            }
            case 9: {
                s.begin_defer(); E.doRemove(x);
                auto old = s.asg; auto opened = s.isopen;
                s.load_state(old, opened);
                break;
            }
            case 10:
                s.close_office(o); // resize_dp uses this direct path.
                check_state(s); ++checks;
                s.open_office(o);
                break;
            }
            check_state(s); ++checks;
        }
    }
    assert(additions > 0);
    printf("coverage state OK: %ld checks, %ld additions, exact=%d, grid=%s\n",
           checks, additions, (int)g_geo_exact, getenv("GEO_INDEX"));
}
